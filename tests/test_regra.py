from datetime import date, timedelta
from decimal import Decimal as D

from anomaly.regra import avaliar

DIA = date(2026, 6, 1)
REF = ['5.60'] * 4 + ['5.80'] * 5 + ['6.00'] * 2 + ['6.20'] * 5 + ['6.40'] * 4


def refs(precos, uf='RJ'):
    return [dict(id=str(i), data=DIA - timedelta(days=1 + i), uf=uf, preco=D(p)) for i, p in enumerate(precos)]


def caso(preco, precos):
    return avaliar(dict(id='x', data=DIA, uf='RJ', preco=D(preco)), refs(precos))


def test_quartis_e_limite_do_exemplo_da_nota():
    a = caso('6.40', REF)
    assert (a.q1, a.q3, a.iqr, a.limite) == (D('5.80'), D('6.20'), D('0.40'), D('6.80'))


def test_cinco_casos_sinteticos():
    assert caso('6.40', REF).situacao == 'sem_alerta'
    assert caso('6.80', REF).situacao == 'sem_alerta'          # igual ao limite nao sinaliza
    assert caso('7.40', REF).situacao == 'acima_da_referencia'
    # O minimo do produto e 10 (a nota usava 20 no teste de bancada): 9 comparaveis nao bastam.
    assert caso('7.40', REF[:9]).motivo == '9 comparaveis, minimo 10'
    assert caso('7.40', ['6.00'] * 20).motivo == 'IQR igual a zero'


def test_janela_exclui_o_proprio_dia_e_outra_uf():
    r = dict(id='x', data=DIA, uf='RJ', preco=D('7'))
    cands = refs(REF) + [dict(id='hoje', data=DIA, uf='RJ', preco=D('1')),
                         dict(id='velho', data=DIA - timedelta(days=366), uf='RJ', preco=D('1')),
                         dict(id='sp', data=DIA - timedelta(days=1), uf='SP', preco=D('1'))]
    a = avaliar(r, cands)
    assert a.n == 20 and not {'hoje', 'velho', 'sp'} & set(a.comparaveis)
    assert (a.janela_inicio, a.janela_fim) == (DIA - timedelta(days=365), DIA - timedelta(days=1))
