"""Passo 2 da secao 5: aplica a limpeza semantica, roda UF/365/10 e BR/90/20 sobre a mesma base
e mede cobertura por UF e concordancia de alertas."""
import json, re, sys, collections, statistics as st
from datetime import timedelta
from alertas import carregar, avaliar, CONFIGS

GESTAO = re.compile(r'gerenciamento|intermedia|sistema informatizado|cart[aã]o (magn|de abast|combust)'
                    r'|gest[aã]o (de|do|da) (abastec|frota)', re.I)


def semantica(x):
    """Classe semantica pelo objeto, quantidade e preco. Nao usa criterio D sozinho."""
    if GESTAO.search(x['objetoCompra'] or ''):
        return 'gestao'
    if x['quantidade'] in (1.0, 12.0) or x['precoUnitario'] == 1.0:
        return 'nao unitario'
    return 'litro'


limpo = carregar(sys.argv[1])
classes = collections.Counter(semantica(x) for x in limpo)
print('Faixa R$2-15 por classe semantica:', dict(classes))
g = [x['precoUnitario'] for x in limpo if semantica(x) == 'gestao']
print(f'Mediana R$/L: gestao {st.median(g):.2f} (n={len(g)}) | litro {st.median(x["precoUnitario"] for x in limpo if semantica(x) == "litro"):.2f}')
for x in limpo:
    if semantica(x) == 'nao unitario':
        print('  nao unitario dentro da faixa:', x['idCompraItem'], x['quantidade'], x['precoUnitario'], x['objetoCompra'][:70].replace('\n', ' '))

for nome, base in (('A: so faixa', limpo), ('B: faixa + sem gestao/nao unitario', [x for x in limpo if semantica(x) == 'litro'])):
    ini = max(r['d'] for r in base) - timedelta(days=182)
    aval = [r for r in base if r['d'] >= ini]
    res = {r['idCompraItem']: {k: avaliar(base, *c, r)[0] for k, c in CONFIGS.items()} for r in aval}
    print(f'\n== Base {nome}: {len(base)} limpos, {len(aval)} avaliados ({ini} a {max(r["d"] for r in base)})')
    for k in CONFIGS:
        c = collections.Counter(v[k] for v in res.values())
        print(f'  {k}: validos {c["ok"] + c["alerta"]}/{len(aval)} ({(c["ok"] + c["alerta"]) / len(aval):.0%}), alertas {c["alerta"]}, insuficiente {c["insuficiente"]}')
    ambos = [i for i, v in res.items() if all(s != 'insuficiente' for s in v.values())]
    a_uf = {i for i in ambos if res[i]['UF/365/10'] == 'alerta'}
    a_br = {i for i in ambos if res[i]['BR/90/20'] == 'alerta'}
    print(f'  Elegiveis nas duas: {len(ambos)} | alertas UF {len(a_uf)} | BR {len(a_br)} | ambas {len(a_uf & a_br)} | so UF {len(a_uf - a_br)} | so BR {len(a_br - a_uf)}')
    uf = collections.defaultdict(collections.Counter)
    for r in aval:
        v = res[r['idCompraItem']]['UF/365/10']
        uf[r['estado']]['n'] += 1; uf[r['estado']]['val'] += v != 'insuficiente'; uf[r['estado']]['al'] += v == 'alerta'
    print('  Cobertura UF/365/10 por UF (validos/avaliados, alertas):',
          ', '.join(f'{u} {c["val"]}/{c["n"]}' + (f' ({c["al"]}a)' if c['al'] else '') for u, c in sorted(uf.items(), key=lambda t: -t[1]['n'])))
    ce = [r for r in base if r['estado'] == 'CE']
    print(f'  CE: {len(ce)} registros na base, {sum(r["d"] >= ini for r in ce)} no periodo avaliado')
