"""Regra IQR superior com referencia da mesma UF. Calculo em Decimal, sem arredondar o limite."""
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

VERSAO = 'iqr-superior-uf-365d-min10-v1'
JANELA_DIAS = 365
MINIMO = 10
K = Decimal('1.5')


def quartil_inc(xs, q):
    """Equivalente ao QUARTIL.INC do Excel: interpolacao linear na posicao (n-1)*q/4."""
    s = sorted(xs)
    h = Decimal(len(s) - 1) * q / 4
    lo = int(h)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (h - lo) * (s[hi] - s[lo])


@dataclass
class Avaliacao:
    situacao: str
    grupo: str
    janela_inicio: date
    janela_fim: date
    n: int
    comparaveis: list = field(default_factory=list)
    q1: Decimal | None = None
    mediana: Decimal | None = None
    q3: Decimal | None = None
    iqr: Decimal | None = None
    limite: Decimal | None = None
    motivo: str | None = None


def avaliar(registro, candidatos, janela_dias=JANELA_DIAS, minimo=MINIMO):
    """registro e candidatos: dicts com id, data, uf, preco. Candidatos ja filtrados por classe preco_litro."""
    d = registro['data']
    ini, fim = d - timedelta(days=janela_dias), d - timedelta(days=1)
    comp = [c for c in candidatos if c['uf'] == registro['uf'] and ini <= c['data'] <= fim]
    base = dict(grupo=f"UF:{registro['uf']}", janela_inicio=ini, janela_fim=fim, n=len(comp),
                comparaveis=[c['id'] for c in comp])
    if len(comp) < minimo:
        return Avaliacao('referencia_insuficiente', motivo=f'{len(comp)} comparaveis, minimo {minimo}', **base)
    precos = [c['preco'] for c in comp]
    q1, med, q3 = (quartil_inc(precos, q) for q in (1, 2, 3))
    iqr = q3 - q1
    if iqr == 0:
        return Avaliacao('referencia_insuficiente', motivo='IQR igual a zero', q1=q1, mediana=med, q3=q3, iqr=iqr, **base)
    lim = q3 + K * iqr
    situacao = 'acima_da_referencia' if registro['preco'] > lim else 'sem_alerta'
    return Avaliacao(situacao, q1=q1, mediana=med, q3=q3, iqr=iqr, limite=lim, **base)
