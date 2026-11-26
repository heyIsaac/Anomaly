"""Bancada do papel A4 (PDM 19746, RJ): qualifica, normaliza para R$ por resma de 500 folhas e roda o IQR.

Uso, na raiz do projeto:  uv run python bancada/papel.py dados/2026-11-26-pdm-19746
"""
import collections, json, re, statistics as st, sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from anomaly import regra  # noqa: E402

D = Path(sys.argv[1])
SO_RESMA = '--so-resma' in sys.argv  # compara so embalagens de 500 folhas
FAIXA = (Decimal('10'), Decimal('80'))  # R$ por resma de 500 folhas plausivel
cat = {x['codigoItem']: x['descricaoItem'] for x in json.load(open(D / 'itens_catalogo.json'))['resultado']}


def branco_a4_75(desc):
    return bool(re.search(r'297 X 210', desc) and re.search(r'GRAMATURA: 75 G', desc) and re.search(r'COR: BRANC', desc))


def classificar(x):
    """(classe, motivo, preco_resma)"""
    desc = cat.get(x['codigoItemCatalogo'], '')
    if not branco_a4_75(desc):
        return 'outro_item', 'nao e A4 branco 75 g/m2', None
    if 'RECICLADO' in (x.get('descricaoItem') or '').upper():
        return 'outro_item', 'papel reciclado', None
    if SO_RESMA and not (x['siglaUnidadeFornecimento'] == 'EMB' and x['capacidadeUnidadeFornecimento'] == 500):
        return 'outra_embalagem', 'embalagem diferente de 500 folhas', None
    sig, cap, med = x['siglaUnidadeFornecimento'], Decimal(str(x['capacidadeUnidadeFornecimento'] or 0)), x['siglaUnidadeMedida']
    p = Decimal(str(x['precoUnitario'] or 0))
    if p <= 0:
        return 'indeterminado', 'preco ausente ou nao positivo', None
    if sig == 'EMB' and med == 'FL' and cap > 0:
        folhas = cap
    elif sig == 'FL' and cap == 0:
        folhas = Decimal(1)
    else:
        return 'indeterminado', f'embalagem sem quantidade de folhas ({sig}, {cap:g}, {med})', None
    resma = p / folhas * 500
    if not FAIXA[0] <= resma <= FAIXA[1]:
        return 'indeterminado', f'R$ {resma:.2f} por resma fora da faixa', resma
    if not x['dataCompra']:
        return 'indeterminado', 'sem data', resma
    return 'preco_resma', f'{folhas:g} folhas por unidade', resma


raw = json.load(open(D / 'rj_all.json'))
u = {x['idCompraItem']: x for x in json.loads(json.dumps(raw))}.values()
classes, motivos, linhas = collections.Counter(), collections.Counter(), []
for x in u:
    c, m, r = classificar(x)
    classes[c] += 1
    if c == 'indeterminado':
        motivos[m.split(' (')[0] if 'embalagem' in m else m.split('R$')[0] + ('fora da faixa' if 'faixa' in m else '')] += 1
    if c == 'preco_resma':
        linhas.append(dict(x, resma=r, d=date.fromisoformat(x['dataCompra'])))
print(f'RJ, PDM 19746: {len(raw)} brutos, {len(u)} unicos')
print('classes:', dict(classes))
print('indeterminados por motivo:', dict(motivos))
emb = collections.Counter(int(x['capacidadeUnidadeFornecimento'] or 1) for x in linhas)
print('folhas por unidade (validos):', dict(sorted(emb.items())))
print(f'R$/resma: mediana {st.median(x["resma"] for x in linhas):.2f}, min {min(x["resma"] for x in linhas):.2f}, max {max(x["resma"] for x in linhas):.2f}')

refs = [dict(id=x['idCompraItem'], data=x['d'], uf='RJ', preco=x['resma']) for x in linhas]
fim = max(x['d'] for x in linhas)
for nome, ini in (('ultimos 6 meses', fim - timedelta(days=182)), ('25/05/2025 em diante', date(2025, 5, 25))):
    aval = [r for r in refs if r['data'] >= ini]
    res = [(r, regra.avaliar(r, refs)) for r in aval]
    c = collections.Counter(a.situacao for _, a in res)
    v = c['sem_alerta'] + c['acima_da_referencia']
    print(f'\n{nome} ({ini} a {fim}): {len(aval)} avaliados, {v} com referencia ({v / len(aval):.0%}), '
          f'{c["acima_da_referencia"]} alertas, {c["referencia_insuficiente"]} insuficientes')
    if nome.startswith('ultimos'):
        ns = [a.n for _, a in res]
        print(f'   comparaveis por avaliacao: min {min(ns)}, mediana {st.median(ns)}, max {max(ns)}')
        for r, a in sorted(res, key=lambda t: t[0]['data']):
            if a.situacao == 'acima_da_referencia':
                x = next(y for y in linhas if y['idCompraItem'] == r['id'])
                print(f"   ALERTA {r['id']} {r['data']} {x['municipio']} | {x['nomeOrgao'][:40]} | "
                      f"R$ {x['precoUnitario']} por {x['siglaUnidadeFornecimento']} {x['capacidadeUnidadeFornecimento']:g} "
                      f"-> R$ {r['preco']:.2f}/resma, limite {a.limite:.2f}, n={a.n}")
