from decimal import Decimal as D

from anomaly.categorias import PapelA4

CAT = {1: 'PAPEL PARA IMPRESSÃO FORMATADO, TIPO: SULFITE, TAMANHO (C X L): 297 X 210 MM, GRAMATURA: 75 G/M2, COR: BRANCO',
       2: 'PAPEL PARA IMPRESSÃO FORMATADO, TIPO: SULFITE, TAMANHO (C X L): 297 X 210 MM, GRAMATURA: 75 G/M2, COR: COLORIDO'}
BASE = dict(codigoItemCatalogo=1, siglaUnidadeFornecimento='EMB', capacidadeUnidadeFornecimento=D('500'),
            siglaUnidadeMedida='FL', precoUnitario=D('21.50'), dataCompra='2026-06-01', descricaoItem='PAPEL A4',
            objetoCompra='Aquisição de material de expediente', marca='CHAMEX')


def cls(**kw):
    c = PapelA4()
    c.catalogo = CAT
    return c.classificar({**BASE, **kw})


def test_resma_valida_usa_o_preco_da_resma():
    assert cls() == ('preco_resma', 'resma de 500 folhas', D('21.50'))


def test_outro_codigo_de_catalogo():
    assert cls(codigoItemCatalogo=2)[0] == 'outro_item'


def test_embalagem_de_outro_tamanho_fica_fora():
    assert cls(capacidadeUnidadeFornecimento=D('100'), precoUnitario=D('13.41'))[0] == 'outra_embalagem'


def test_embalagem_sem_numero_de_folhas():
    assert cls(capacidadeUnidadeFornecimento=D('0'))[0] == 'indeterminado'


def test_reciclado_na_descricao_e_couche_no_objeto():
    assert cls(descricaoItem='PAPEL ... TIPO: RECICLADO')[0] == 'outro_item'
    assert cls(objetoCompra='Objeto: Pregão Eletrônico - Aquisição de papel couchê.')[0] == 'outro_item'


def test_objeto_com_varios_materiais_nao_exclui_a_resma():
    # Caso real: objeto cita "adesivo PVA e outros" e a linha e uma resma comum.
    assert cls(objetoCompra='Aquisição de adesivo PVA extra forte e outros')[0] == 'preco_resma'
    assert cls(objetoCompra='Aquisição de papel A4, papel couchê e envelopes')[0] == 'preco_resma'


def test_preco_fora_da_faixa():
    assert cls(precoUnitario=D('120'))[0] == 'indeterminado'
