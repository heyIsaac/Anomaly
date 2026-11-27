"""Aceite da categoria papel A4 (parte Python + banco), com origem so pelo cache."""
from datetime import date
from decimal import Decimal as D
from pathlib import Path

import psycopg
import pytest

from anomaly.importar import DSN, importar

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / 'dados/2026-11-26-pdm-19746'


@pytest.fixture(scope='module')
def lote():
    try:
        conn = psycopg.connect(DSN, connect_timeout=3)
    except psycopg.OperationalError:
        pytest.fail('Postgres indisponivel: rode `docker compose up -d`')
    with conn:
        lote_id, *_ = importar(conn, DADOS / 'rj_all.json', 'RJ', date(2026, 11, 26), RAIZ / 'dados/2026-11-26-origem-papel',
                               rede=False, categoria='papel-a4', catalogo=DADOS / 'itens_catalogo.json')
        yield conn, lote_id
        conn.execute('DELETE FROM lote WHERE id=%s', (lote_id,))
        conn.commit()


def test_lote_descreve_a_categoria(lote):
    conn, lote_id = lote
    row = conn.execute('SELECT categoria, unidade_comparacao, codigo_tipo, catmat FROM lote WHERE id=%s', (lote_id,)).fetchone()
    assert row == ('papel-a4', 'resma de 500 folhas', 'PDM', 19746)


def test_resma_da_marinha(lote):
    conn, lote_id = lote
    preco, limite, n, sit, origem = conn.execute(
        'SELECT a.preco_observado, a.limite, a.n, a.situacao, r.origem_status FROM avaliacao a'
        ' JOIN registro r USING (lote_id, id_compra_item) WHERE a.lote_id=%s AND a.id_compra_item=%s',
        (lote_id, '7732020600022202600008')).fetchone()
    assert (preco, round(limite, 2), n, sit, origem) == (D('33.7'), D('29.59'), 120, 'acima_da_referencia', 'confirmada')


def test_casos_conferidos_na_origem_ficam_fora_da_referencia(lote):
    conn, lote_id = lote
    c = dict(conn.execute('SELECT id_compra_item, classe FROM registro WHERE lote_id=%s AND id_compra_item = ANY(%s)',
                          (lote_id, ['9268500590022202600001', '1531670500107202600311', '1603170590001202600036',
                                     '7321000590008202500036'])).fetchall())
    assert c == {'9268500590022202600001': 'outro_item',      # papel couche sob codigo de sulfite
                 '1531670500107202600311': 'outro_item',      # reciclado
                 '1603170590001202600036': 'outro_item',      # papel de certificado
                 '7321000590008202500036': 'outra_embalagem'}  # pacote de 150 folhas


def test_contagens(lote):
    conn, lote_id = lote
    c = dict(conn.execute('SELECT classe, count(*) FROM registro WHERE lote_id=%s GROUP BY 1', (lote_id,)).fetchall())
    assert c == {'preco_resma': 517, 'outro_item': 690, 'outra_embalagem': 26, 'indeterminado': 78}
