"""Busca no PNCP (modulo-contratacoes 2.1) o item de origem de cada idCompraItem e guarda em cache."""
import json, os, sys, time, urllib.request, urllib.error

CACHE = os.path.join(os.path.dirname(__file__), '..', 'dados', '2026-11-26-origem')
URL = ('https://dadosabertos.compras.gov.br/modulo-contratacoes/'
       '2.1_consultarItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={}')


def itens_da_compra(id_compra):
    path = os.path.join(CACHE, f'{id_compra}.json')
    if not os.path.exists(path):
        try:
            with urllib.request.urlopen(URL.format(id_compra), timeout=60) as r:
                body = json.load(r)
        except urllib.error.HTTPError as e:
            body = {'erro': e.code}
        json.dump(body, open(path, 'w'), ensure_ascii=False)
        time.sleep(0.3)
    return json.load(open(path))


def origem(rec):
    body = itens_da_compra(rec['idCompra'])
    for it in body.get('resultado') or []:
        if it['idCompraItem'] == rec['idCompraItem']:
            return it
    return {'erro': body.get('erro', 'item ausente na compra')}


def link_pncp(numero_controle):
    # 00394502000144-1-011884/2026 -> https://pncp.gov.br/app/editais/00394502000144/2026/11884
    cnpj, _, resto = numero_controle.split('-', 2)
    seq, ano = resto.split('/')
    return f'https://pncp.gov.br/app/editais/{cnpj}/{ano}/{int(seq)}'


if __name__ == '__main__':
    os.makedirs(CACHE, exist_ok=True)
    ids = set(sys.argv[2:])
    for rec in json.load(open(sys.argv[1])):
        if rec['idCompraItem'] in ids:
            o = origem(rec)
            print(rec['idCompraItem'], json.dumps({k: o.get(k) for k in (
                'erro', 'descricaoResumida', 'unidadeMedida', 'situacaoCompraItemNome', 'quantidadeResultado',
                'valorUnitarioResultado', 'valorTotalResultado', 'criterioJulgamentoNome', 'numeroControlePNCPCompra')},
                ensure_ascii=False))
