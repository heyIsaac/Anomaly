"""Lista os alertas das configuracoes UF/365/10 e BR/90/20 no periodo avaliado (ultimos 6 meses)."""
import json, sys
from datetime import date, timedelta


def quartil_inc(xs, q):  # mesmo QUARTIL.INC da bancada.py
    s = sorted(xs); h = (len(s) - 1) * q / 4; lo = int(h)
    return s[lo] + (h - lo) * (s[min(lo + 1, len(s) - 1)] - s[lo])

CONFIGS = {'UF/365/10': ('uf', 365, 10), 'BR/90/20': ('br', 90, 20)}


def carregar(path, excluir=frozenset()):
    raw = json.load(open(path))
    out = []
    for x in {x['idCompraItem']: x for x in raw}.values():
        p = x['precoUnitario']
        if (x['siglaUnidadeFornecimento'] != 'L' or not p or p <= 0 or not 2 <= p <= 15
                or not x['dataCompra'] or not x['codigoMunicipio'] or x['idCompraItem'] in excluir):
            continue
        out.append(dict(x, d=date.fromisoformat(x['dataCompra'])))
    return out


def avaliar(limpo, grupo, jan, mn, r):
    ref = [o['precoUnitario'] for o in limpo if r['d'] - timedelta(days=jan) <= o['d'] < r['d']
           and (grupo == 'br' or o['estado'] == r['estado'])]
    if len(ref) < mn:
        return 'insuficiente', len(ref), None
    q1, q3 = quartil_inc(ref, 1), quartil_inc(ref, 3)
    if q3 == q1:
        return 'insuficiente', len(ref), None
    lim = round(q3 + 1.5 * (q3 - q1), 2)
    return ('alerta' if r['precoUnitario'] > lim else 'ok'), len(ref), (round(q1, 3), round(q3, 3), lim)


if __name__ == '__main__':
    limpo = carregar(sys.argv[1])
    ini = max(r['d'] for r in limpo) - timedelta(days=182)
    for r in (r for r in limpo if r['d'] >= ini):
        res = {k: avaliar(limpo, *c, r) for k, c in CONFIGS.items()}
        if any(v[0] == 'alerta' for v in res.values()):
            print(r['idCompraItem'], r['d'], r['estado'], r['precoUnitario'], r['criterioJulgamento'],
                  {k: v[0] + f' n={v[1]} lim={v[2] and v[2][2]}' for k, v in res.items()})
