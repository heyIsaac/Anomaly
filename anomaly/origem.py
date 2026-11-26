"""Conferencia do item no PNCP (modulo-contratacoes 2.1), com cache em disco por idCompra."""
import http.client, json, time, urllib.error, urllib.request
from pathlib import Path

URL = ('https://dadosabertos.compras.gov.br/modulo-contratacoes/'
       '2.1_consultarItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={}')

TRANSITORIOS = {408, 425, 429, 500, 502, 503, 504}


def _baixar(id_compra, tentativas=3, espera=2):
    """Devolve o corpo JSON, {'erro': 404} para ausencia definitiva ou None para falha transitoria."""
    for t in range(tentativas):
        try:
            with urllib.request.urlopen(URL.format(id_compra), timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code not in TRANSITORIOS:
                return {'erro': e.code}
        except (OSError, http.client.HTTPException):  # URLError, timeout, conexao derrubada
            pass
        if t + 1 < tentativas:
            time.sleep(espera * (t + 1))
    return None


def itens_da_compra(id_compra, cache: Path, rede=True):
    """So respostas definitivas (sucesso ou 4xx nao transitorio) vao para o cache."""
    path = cache / f'{id_compra}.json'
    if path.exists():
        return json.loads(path.read_text())
    if not rede:
        return None
    body = _baixar(id_compra)
    if body is None:
        return {'erro': 'transitorio'}
    cache.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, ensure_ascii=False))
    time.sleep(0.3)
    return body


def conferir(id_compra, id_compra_item, cache: Path, rede=True):
    """Devolve (status, numero_controle_pncp)."""
    body = itens_da_compra(id_compra, cache, rede)
    if body is None:
        return 'nao_consultada', None
    if 'erro' in body and not body.get('resultado'):
        return ('ausente_no_pncp', None) if body['erro'] == 404 else ('erro', None)
    for it in body.get('resultado') or []:
        if it.get('idCompraItem') == id_compra_item:
            return 'confirmada', it.get('numeroControlePNCPCompra')
    return 'ausente_no_pncp', None


def link_pncp(numero_controle):
    """00394502000144-1-011884/2026 -> https://pncp.gov.br/app/editais/00394502000144/2026/11884"""
    cnpj, _, resto = numero_controle.split('-', 2)
    seq, ano = resto.split('/')
    return f'https://pncp.gov.br/app/editais/{cnpj}/{ano}/{int(seq)}'
