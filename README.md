# ANOMALY · importação e análise

Importador Python do piloto ANOMALY: gasolina comum (CATMAT 461506) do Compras.gov.br,
referência estadual por IQR, piloto no RJ. Notas do projeto no vault Obsidian:
`estudos/jala/estatistica/anomaly/ANOMALY.md`.

## Rodar

```bash
docker compose up -d                 # Postgres 17 em 127.0.0.1:5433 (usuario/banco anomaly)
uv sync
uv run anomaly-import dados/2026-11-26-catmat-461506/br_all.json --uf RJ --extraido-em 2026-11-26
uv run anomaly-import dados/2026-11-26-pdm-19746/rj_all.json --categoria papel-a4 \
    --catalogo dados/2026-11-26-pdm-19746/itens_catalogo.json --cache-origem dados/2026-11-26-origem-papel \
    --uf RJ --extraido-em 2026-11-26
uv run pytest                        # inclui o aceite de Mangaratiba (precisa do Postgres no ar)
```

`--sem-rede` confere a origem só pelo cache em `dados/2026-11-26-origem/`.
`DATABASE_URL` sobrescreve a conexão padrão.

## O que o importador faz

1. Lê a extração, guarda o hash do arquivo em `lote` e uma linha por `idCompraItem` em `registro`, com o JSON bruto.
2. Classifica cada valor conforme a categoria (`anomaly/categorias.py`). Gasolina: `preco_litro`, `gestao`, `nao_unitario`, `indeterminado`. Papel A4 (PDM 19746): `preco_resma` (só embalagens de 500 folhas), `outro_item` (outro código, reciclado, couchê, certificado), `outra_embalagem`, `indeterminado`. Cada registro guarda o motivo e o preço na unidade de comparação (`preco_normalizado`).
3. Avalia os registros `preco_litro` da UF do piloto (`anomaly/regra.py`, versão `iqr-superior-uf-365d-min10-v1`):
   comparáveis da mesma UF nos 365 dias anteriores, mínimo 10, alerta se o preço for maior que Q3 + 1,5 × IQR.
   O limite é guardado exato em `numeric`; a tela formata em duas casas.
4. Grava `avaliacao` e os comparáveis usados em `avaliacao_comparavel`.
5. Confere a origem no PNCP (`anomaly/origem.py`) e grava `numero_controle_pncp` e `origem_status`.

## Pastas

- `anomaly/`: pacote do importador. `db/schema.sql`: schema (aplicado pelo importador, idempotente).
- `bancada/`: scripts da bancada de 2026-11-26 (rodar de dentro de `bancada/` ou com o caminho dos dados).
- `dados/`: extrações brutas e cache do PNCP. Não editar à mão.

## Web (`web/`)

Next.js 16 (App Router, Cache Components) com Tailwind. Lê o lote mais recente de cada categoria com um papel somente leitura; a lista tem uma aba por categoria (`?categoria=papel-a4`).

```bash
docker compose exec -T db psql -U anomaly -d anomaly < db/leitura.sql   # uma vez: cria anomaly_leitura
cd web && pnpm install && pnpm dev                                         # http://localhost:3000
```

`DATABASE_URL_LEITURA` sobrescreve a conexão. Rotas: `/` (lista, filtros `situacao` e `municipio`) e
`/compras/<idCompraItem>` (detalhe com régua de evidência, números da referência, objeto, origem e comparáveis).
