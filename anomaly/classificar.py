"""Classificacao semantica do valor em precoUnitario antes de qualquer calculo.

So `preco_litro` entra na referencia. As demais classes guardam o motivo para aparecer
no resumo da carga. Criterio D, quantidade 1 ou 12 e preco fora da faixa sao pistas de
revisao: sozinhas nao decidem a exclusao, exceto quando a regra abaixo diz isso.
"""
import re
from decimal import Decimal

FAIXA = (Decimal('2'), Decimal('15'))  # R$/L plausivel para gasolina comum no periodo
GESTAO = re.compile(r'gerenciamento|intermedia|sistema informatizado|cart[aã]o (magn|de abast|combust)'
                    r'|gest[aã]o (de|do|da) (abastec|frota)', re.I)


def pistas(x):
    p, q = x.get('precoUnitario'), x.get('quantidade')
    out = []
    if (x.get('criterioJulgamento') or '').strip() == 'D':
        out.append('criterio de julgamento por desconto')
    if q in (1, 12):
        out.append(f'quantidade {q:g}')
    if p is not None and p > 0 and not FAIXA[0] <= p <= FAIXA[1]:
        out.append('preco fora da faixa de R$ 2 a R$ 15 por litro')
    return out


def classificar(x):
    """Devolve (classe, motivo). Ordem: unidade, preco, objeto, quantidade, faixa, campos."""
    p, q = x.get('precoUnitario'), x.get('quantidade')
    if x.get('siglaUnidadeFornecimento') != 'L':
        return 'indeterminado', f"unidade de fornecimento {x.get('siglaUnidadeFornecimento')!r}, nao litro"
    if p is None or p <= 0:
        return 'indeterminado', 'preco ausente ou nao positivo'
    m = GESTAO.search(x.get('objetoCompra') or '')
    if m:
        return 'gestao', f"objeto da compra cita '{m.group(0)}': contrato de gestao de abastecimento"
    if q in (1, 12):
        return 'nao_unitario', f'quantidade {q:g}: o preco provavelmente e valor global ou mensal'
    if p == 1:
        return 'nao_unitario', 'preco R$ 1,00: a quantidade provavelmente e o orcamento em reais'
    if not FAIXA[0] <= p <= FAIXA[1]:
        return 'indeterminado', f'preco R$ {p} fora da faixa de R$ 2 a R$ 15 por litro'
    if not x.get('dataCompra'):
        return 'indeterminado', 'sem data da compra'
    if not x.get('codigoMunicipio'):
        return 'indeterminado', 'sem municipio do comprador'
    return 'preco_litro', 'preco por litro de gasolina comum'
