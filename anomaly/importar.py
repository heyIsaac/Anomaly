"""CLI: importa uma extracao do Compras.gov.br, classifica, avalia a UF do piloto e persiste.

Exemplo:
    uv run anomaly-import dados/2026-11-26-catmat-461506/br_all.json --uf RJ --extraido-em 2026-11-26
"""
import argparse, hashlib, json, os, sys
from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from . import regra
from .classificar import VERSAO as VERSAO_CLASSES, classificar, pistas
from .origem import conferir

DSN = os.environ.get('DATABASE_URL', 'postgresql://anomaly:anomaly-local@127.0.0.1:5433/anomaly')
FONTE = 'compras.gov.br modulo-pesquisa-preco/1_consultarMaterial'
SCHEMA = Path(__file__).resolve().parent.parent / 'db' / 'schema.sql'


def ler(arquivo: Path):
    texto = arquivo.read_text()
    brutos = json.loads(texto)                          # fiel ao arquivo, vai para jsonb
    exatos = json.loads(texto, parse_float=Decimal)     # mesmo conteudo, numeros exatos para o calculo
    # Uma observacao por idCompraItem; a ultima ocorrencia vence, como na bancada.
    unicos = {}
    for b, x in zip(brutos, exatos):
        unicos[x['idCompraItem']] = (b, x)
    return texto, len(brutos), unicos


def importar(conn, arquivo: Path, uf: str, extraido_em: date, cache: Path, rede: bool, catmat=None):
    texto, total, unicos = ler(arquivo)
    catmat = catmat or Counter(x['codigoItemCatalogo'] for _, x in unicos.values()).most_common(1)[0][0]
    with conn.cursor() as cur:
        cur.execute(SCHEMA.read_text())
        cur.execute('INSERT INTO lote (fonte, catmat, arquivo, sha256, extraido_em, total_bruto, total_unico, versao_classificacao)'
                    ' VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id',
                    (FONTE, catmat, str(arquivo), hashlib.sha256(texto.encode()).hexdigest(),
                     extraido_em, total, len(unicos), VERSAO_CLASSES))
        lote = cur.fetchone()[0]

        classes, refs = Counter(), []
        linhas = []
        for b, x in unicos.values():
            classe, motivo = classificar(x)
            classes[classe] += 1
            d = date.fromisoformat(x['dataCompra']) if x.get('dataCompra') else None
            linhas.append((lote, x['idCompraItem'], str(x['idCompra']), d, x.get('estado'), x.get('codigoMunicipio'),
                           x.get('municipio'), x.get('codigoUasg'), x.get('nomeOrgao'), x.get('codigoItemCatalogo'),
                           x.get('siglaUnidadeFornecimento'), x.get('quantidade'), x.get('precoUnitario'),
                           x.get('criterioJulgamento'), x.get('objetoCompra'), classe, motivo, pistas(x), Jsonb(b)))
            if classe == 'preco_litro':
                refs.append(dict(id=x['idCompraItem'], id_compra=str(x['idCompra']), data=d,
                                 uf=x.get('estado'), preco=x['precoUnitario']))
        cur.executemany(
            'INSERT INTO registro (lote_id, id_compra_item, id_compra, data_compra, uf, codigo_municipio, municipio,'
            ' codigo_uasg, nome_orgao, catmat, unidade, quantidade, preco_unitario, criterio, objeto, classe,'
            ' motivo_classe, pistas_revisao, bruto) VALUES (' + ','.join(['%s'] * 19) + ')', linhas)

        situacoes = Counter()
        alvo = [r for r in refs if r['uf'] == uf]
        for r in alvo:
            a = regra.avaliar(r, refs)
            situacoes[a.situacao] += 1
            cur.execute(
                'INSERT INTO avaliacao (lote_id, id_compra_item, versao_regra, grupo, janela_inicio, janela_fim, minimo,'
                ' n, q1, mediana, q3, iqr, limite, preco_observado, situacao, motivo)'
                ' VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id',
                (lote, r['id'], regra.VERSAO, a.grupo, a.janela_inicio, a.janela_fim, regra.MINIMO, a.n,
                 a.q1, a.mediana, a.q3, a.iqr, a.limite, r['preco'], a.situacao, a.motivo))
            av = cur.fetchone()[0]
            cur.executemany('INSERT INTO avaliacao_comparavel VALUES (%s,%s,%s)',
                            [(av, lote, c) for c in a.comparaveis])
            status, controle = conferir(r['id_compra'], r['id'], cache, rede)
            cur.execute('UPDATE registro SET origem_status=%s, numero_controle_pncp=%s'
                        ' WHERE lote_id=%s AND id_compra_item=%s', (status, controle, lote, r['id']))
    conn.commit()
    return lote, total, len(unicos), classes, situacoes


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('arquivo', type=Path)
    ap.add_argument('--uf', default='RJ', help='UF do piloto avaliada (padrao RJ)')
    ap.add_argument('--extraido-em', type=date.fromisoformat, required=True)
    ap.add_argument('--cache-origem', type=Path, default=Path('dados/2026-11-26-origem'))
    ap.add_argument('--sem-rede', action='store_true', help='confere origem so pelo cache, sem chamar o PNCP')
    a = ap.parse_args(argv)
    with psycopg.connect(DSN) as conn:
        lote, total, unicos, classes, situacoes = importar(conn, a.arquivo, a.uf, a.extraido_em,
                                                           a.cache_origem, not a.sem_rede)
    print(f'lote {lote}: {total} brutos, {unicos} unicos')
    print('classes:', dict(classes))
    print(f'avaliacoes {a.uf} ({regra.VERSAO}):', dict(situacoes))


if __name__ == '__main__':
    sys.exit(main())
