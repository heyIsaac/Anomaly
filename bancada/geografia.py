"""Isola o efeito da geografia: UF vs BR com mesma janela e mesmo minimo, na Base B."""
import contextlib, io, sys, collections
from datetime import timedelta
with contextlib.redirect_stdout(io.StringIO()):
    import revisao as R
base = [x for x in R.limpo if R.semantica(x) == 'litro']
ini = max(r['d'] for r in base) - timedelta(days=182)
aval = [r for r in base if r['d'] >= ini]
for jan, mn in ((365, 10), (90, 20), (180, 10)):
    res = {r['idCompraItem']: (r, {g: R.avaliar(base, g, jan, mn, r) for g in ('uf', 'br')}) for r in aval}
    ok = {i: v for i, v in res.items() if all(s[0] != 'insuficiente' for s in v[1].values())}
    au = {i for i, v in ok.items() if v[1]['uf'][0] == 'alerta'}; ab = {i for i, v in ok.items() if v[1]['br'][0] == 'alerta'}
    vu = sum(v[1]['uf'][0] != 'insuficiente' for v in res.values())
    print(f'\n{jan}d min{mn}: avaliados {len(aval)} | UF validos {vu} | BR validos {len(aval)} | elegiveis nas duas {len(ok)} | alerta UF {len(au)} BR {len(ab)} ambas {len(au & ab)} so UF {len(au - ab)} so BR {len(ab - au)}')
    for i in sorted(au | ab):
        r, v = ok[i]
        print(f"   {r['estado']} {r['municipio'][:16]:16} {r['precoUnitario']:5}  UF {v['uf'][0]:6} n={v['uf'][1]:3} lim={v['uf'][2][2]}  BR {v['br'][0]:6} n={v['br'][1]:3} lim={v['br'][2][2]}")
