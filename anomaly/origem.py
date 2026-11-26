"""Conferencia do item no PNCP (modulo-contratacoes 2.1), com cache em disco por idCompra."""
import http.client, json, time, urllib.error, urllib.request
from pathlib import Path

URL = ('https://dadosabertos.compras.gov.br/modulo-contratacoes/'
       '2.1_consultarItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={}')


def itens_da_compra(id_compra, cache: Path, rede=True):
    path = cache / f'{id_compra}.json'
    if not path.exists():
        if not rede:
            return None
        for tentativa in range(2):
            try:
                with urllib.request.urlopen(URL.format(id_compra), timeout=60) as r:
                    body = json.load(r)
                break
            except urllib.error.HTTPError as e:
                body = {'erro': e.code}
                break
            except (OSError, http.client.HTTPException) as e:  # URLError, timeout, conexao derrubada
                if tentativa:
                    return {'erro': f'rede: {e}'}  # falha de rede nao vai para o cache
                time.sleep(2)
        cache.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(body, ensure_ascii=False))
        time.sleep(0.3)
    return json.loads(path.read_text())


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
