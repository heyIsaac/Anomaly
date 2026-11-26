"""Aceite ponta a ponta (parte Python + banco): Mangaratiba e equivalencia com a bancada."""
import os
from datetime import date
from decimal import Decimal as D
from pathlib import Path

import psycopg
import pytest

from anomaly.importar import DSN, importar

RAIZ = Path(__file__).resolve().parent.parent
ARQ = RAIZ / 'dados/2026-11-26-catmat-461506/br_all.json'
CACHE = RAIZ / 'dados/2026-11-26-origem'
ITEM = '7331000600057202600002'


@pytest.fixture(scope='module')
def lote():
    try:
        conn = psycopg.connect(DSN, connect_timeout=3)
    except psycopg.OperationalError:
        pytest.fail('Postgres indisponivel: rode `docker compose up -d`')
    with conn:
        lote_id, *_ = importar(conn, ARQ, 'RJ', date(2026, 11, 26), CACHE, rede=False)
        yield conn, lote_id
        conn.execute('DELETE FROM lote WHERE id=%s', (lote_id,))
        conn.commit()


def test_mangaratiba(lote):
    conn, lote_id = lote
    row = conn.execute(
        'SELECT a.preco_observado, a.limite, a.n, a.grupo, a.janela_inicio, a.janela_fim, a.situacao,'
        ' r.objeto, r.origem_status, r.numero_controle_pncp, a.id'
        ' FROM avaliacao a JOIN registro r USING (lote_id, id_compra_item)'
        ' WHERE a.lote_id=%s AND a.id_compra_item=%s', (lote_id, ITEM)).fetchone()
    preco, limite, n, grupo, ini, fim, situacao, objeto, origem, controle, av = row
    assert preco == D('7.99')
    assert round(limite, 2) == D('7.75')
    assert n == 18 and grupo == 'UF:RJ'
    assert (ini, fim) == (date(2025, 9, 16), date(2026, 9, 15))
    assert situacao == 'acima_da_referencia'
    assert 'Gasolina Comum' in objeto
    assert origem == 'confirmada' and controle == '00394502000144-1-011884/2026'
    comp = conn.execute(
        'SELECT r.uf, r.classe, r.data_compra FROM avaliacao_comparavel c'
        ' JOIN registro r ON r.lote_id=c.lote_id AND r.id_compra_item=c.id_compra_item WHERE c.avaliacao_id=%s',
        (av,)).fetchall()
    assert len(comp) == 18 and all(u == 'RJ' and cl == 'preco_litro' and ini <= d <= fim for u, cl, d in comp)


def test_cobertura_rj_no_periodo_da_bancada(lote):
    conn, lote_id = lote
    rows = conn.execute(
        "SELECT a.situacao FROM avaliacao a JOIN registro r USING (lote_id, id_compra_item)"
        " WHERE a.lote_id=%s AND r.data_compra >= '2026-05-25'", (lote_id,)).fetchall()
    assert len(rows) == 20 and all(s != 'referencia_insuficiente' for (s,) in rows)


def test_tres_situacoes_presentes(lote):
    conn, lote_id = lote
    s = {x for (x,) in conn.execute('SELECT DISTINCT situacao FROM avaliacao WHERE lote_id=%s', (lote_id,))}
    assert s == {'acima_da_referencia', 'sem_alerta', 'referencia_insuficiente'}


def test_classes_da_base_b(lote):
    conn, lote_id = lote
    c = dict(conn.execute('SELECT classe, count(*) FROM registro WHERE lote_id=%s GROUP BY 1', (lote_id,)).fetchall())
    # Base B (1602) + 3 registros do PR com quantidade 1 e preco plausivel, que a v1 excluia.
    assert c['preco_litro'] == 1605
