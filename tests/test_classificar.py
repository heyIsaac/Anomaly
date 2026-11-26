from decimal import Decimal as D

from anomaly.classificar import classificar, pistas

BASE = dict(siglaUnidadeFornecimento='L', quantidade=D('1000'), precoUnitario=D('6.25'), dataCompra='2026-03-17',
            codigoMunicipio=2307304, criterioJulgamento='D', objetoCompra='Aquisicao de gasolina comum')


def c(**kw):
    return classificar({**BASE, **kw})[0]


def test_criterio_d_sozinho_nao_exclui():
    assert c() == 'preco_litro'
    assert 'criterio de julgamento por desconto' in pistas(BASE)


def test_gestao_pelo_objeto():
    assert c(objetoCompra='Servicos de gerenciamento de abastecimento de combustiveis') == 'gestao'


def test_nao_unitario():
    assert c(quantidade=D('1'), precoUnitario=D('696654')) == 'nao_unitario'
    assert c(quantidade=D('12'), precoUnitario=D('6.50')) == 'nao_unitario'
    assert c(precoUnitario=D('1.0'), quantidade=D('255023')) == 'nao_unitario'


def test_indeterminado():
    assert c(precoUnitario=D('0.497'), quantidade=D('140000')) == 'indeterminado'
    assert c(siglaUnidadeFornecimento='UN') == 'indeterminado'
    assert c(dataCompra=None) == 'indeterminado'
