"""Bancada do IQR do ANOMALY: casos sinteticos + cobertura na base real (CATMAT 461506)."""
import json, sys, collections
from datetime import date, timedelta

def quartil_inc(xs, q):  # equivalente ao QUARTIL.INC do Excel (interpolacao linear, n-1)
    s = sorted(xs); h = (len(s) - 1) * q / 4; lo = int(h)
    return s[lo] + (h - lo) * (s[min(lo + 1, len(s) - 1)] - s[lo])

def avalia(preco, ref, min_n=20):
    if len(ref) < min_n: return 'referencia insuficiente (n<min)', None
    q1, q3 = quartil_inc(ref, 1), quartil_inc(ref, 3); iqr = q3 - q1
    if iqr == 0: return 'referencia insuficiente (IQR=0)', None
    lim = round(q3 + 1.5 * iqr, 2)
    return ('preco acima da referencia' if preco > lim else 'sem alerta'), (q1, q3, iqr, lim)

# ---- 1. casos sinteticos do ANOMALY.md
ref = [5.60]*4 + [5.80]*5 + [6.00]*2 + [6.20]*5 + [6.40]*4
print('Sintetico Q1,Q3,IQR,lim =', avalia(0, ref)[1])
casos = [(6.40, ref, 'sem alerta'), (6.80, ref, 'sem alerta'), (7.40, ref, 'preco acima da referencia'),
         (7.40, ref[:19], 'referencia insuficiente (n<min)'), (7.40, [6.0]*20, 'referencia insuficiente (IQR=0)')]
for p, r, esp in casos:
    got = avalia(p, r)[0]; print(f'  {p:.2f} n={len(r):2d} -> {got:35s} {"OK" if got == esp else "FALHOU: esperado " + esp}')

# ---- 2. base real
raw = json.load(open(sys.argv[1]))
uf = sys.argv[2] if len(sys.argv) > 2 else None
dedup = {x['idCompraItem']: x for x in raw}.values()
limpo, isolados = [], collections.Counter()
for x in dedup:
    if uf and x['estado'] != uf: continue
    if x['siglaUnidadeFornecimento'] != 'L': isolados['unidade != L'] += 1; continue
    if not x['precoUnitario'] or x['precoUnitario'] <= 0: isolados['preco <= 0'] += 1; continue
    if not (2 <= x['precoUnitario'] <= 15): isolados['preco fora de 2..15 R$/L (provavel erro)'] += 1; continue
    if not x['dataCompra']: isolados['sem data'] += 1; continue
    if not x['codigoMunicipio']: isolados['sem municipio'] += 1; continue
    limpo.append(dict(d=date.fromisoformat(x['dataCompra']), mun=x['codigoMunicipio'], uf=x['estado'], p=x['precoUnitario']))
print(f'\nBase {uf or "BR"}: limpos={len(limpo)} isolados={dict(isolados)}')
dmax = max(r['d'] for r in limpo)
ini = dmax - timedelta(days=182)  # periodo avaliado = ultimos 6 meses da base
aval = [r for r in limpo if r['d'] >= ini]
print(f'Periodo avaliado {ini} -> {dmax}: {len(aval)} registros')

print(f'\n{"grupo":10s} {"janela":>6s} {"min":>4s} {"validos":>8s} {"cobert":>7s} {"alertas":>7s}  motivos')
for grupo in ('mun', 'uf', 'br'):
    for jan in (90, 180, 365):
        for mn in (10, 20):
            st = collections.Counter()
            for r in aval:
                ref = [o['p'] for o in limpo if r['d'] - timedelta(days=jan) <= o['d'] < r['d']
                       and (grupo == 'br' or o[grupo] == r[grupo])]
                st[avalia(r['p'], ref, mn)[0]] += 1
            v = st['sem alerta'] + st['preco acima da referencia']
            mot = {k.split('(')[1][:-1]: n for k, n in st.items() if 'insuf' in k}
            print(f'{grupo:10s} {jan:6d} {mn:4d} {v:8d} {v/len(aval):7.0%} {st["preco acima da referencia"]:7d}  {mot}')
