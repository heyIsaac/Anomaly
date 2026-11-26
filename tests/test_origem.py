import io, json, urllib.error

import pytest

from anomaly import origem


class Resp(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): self.close()


def ok_body():
    return Resp(json.dumps({'resultado': [{'idCompraItem': 'I1', 'numeroControlePNCPCompra': 'X-1-000001/2026'}]}).encode())


def http_err(code):
    return urllib.error.HTTPError('u', code, 'x', {}, None)


@pytest.fixture(autouse=True)
def sem_espera(monkeypatch):
    monkeypatch.setattr(origem.time, 'sleep', lambda s: None)


def fake(monkeypatch, respostas):
    chamadas = []
    def urlopen(url, timeout):
        chamadas.append(url)
        r = respostas.pop(0)
        if isinstance(r, Exception): raise r
        return r()
    monkeypatch.setattr(origem.urllib.request, 'urlopen', urlopen)
    return chamadas


def test_503_persistente_nao_vai_para_o_cache(monkeypatch, tmp_path):
    chamadas = fake(monkeypatch, [http_err(503)] * 3 + [ok_body])
    assert origem.conferir('C1', 'I1', tmp_path) == ('erro', None)
    assert not list(tmp_path.iterdir())
    assert origem.conferir('C1', 'I1', tmp_path) == ('confirmada', 'X-1-000001/2026')  # nova consulta
    assert len(chamadas) == 4


def test_503_seguido_de_sucesso_na_mesma_consulta(monkeypatch, tmp_path):
    fake(monkeypatch, [http_err(503), ConnectionResetError(), ok_body])
    assert origem.conferir('C1', 'I1', tmp_path)[0] == 'confirmada'


def test_404_e_definitivo_e_fica_no_cache(monkeypatch, tmp_path):
    chamadas = fake(monkeypatch, [http_err(404)])
    assert origem.conferir('C1', 'I1', tmp_path) == ('ausente_no_pncp', None)
    assert origem.conferir('C1', 'I1', tmp_path) == ('ausente_no_pncp', None)
    assert len(chamadas) == 1


def test_sem_rede_e_sem_cache_fica_pendente(tmp_path):
    assert origem.conferir('C1', 'I1', tmp_path, rede=False) == ('nao_consultada', None)
