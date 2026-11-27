-- ANOMALY: lotes de importacao, registros classificados e avaliacoes IQR persistidas.
-- Valores monetarios em numeric para guardar o calculo exato; a tela formata em duas casas.

CREATE TABLE IF NOT EXISTS lote (
    id            serial PRIMARY KEY,
    fonte         text        NOT NULL,          -- ex.: compras.gov.br modulo-pesquisa-preco 1_consultarMaterial
    catmat        integer     NOT NULL,
    arquivo       text        NOT NULL,
    sha256        text        NOT NULL,
    extraido_em   date        NOT NULL,
    carregado_em  timestamptz NOT NULL DEFAULT now(),
    total_bruto   integer     NOT NULL,
    total_unico   integer     NOT NULL,
    versao_classificacao text NOT NULL DEFAULT 'classes-v1'
);
ALTER TABLE lote ADD COLUMN IF NOT EXISTS versao_classificacao text NOT NULL DEFAULT 'classes-v1';

-- Classe semantica do valor: so preco_litro entra no calculo da referencia.
CREATE TABLE IF NOT EXISTS registro (
    lote_id          integer NOT NULL REFERENCES lote(id) ON DELETE CASCADE,
    id_compra_item   text    NOT NULL,
    id_compra        text    NOT NULL,
    data_compra      date,
    uf               text,
    codigo_municipio integer,
    municipio        text,
    codigo_uasg      text,
    nome_orgao       text,
    catmat           integer,
    unidade          text,
    quantidade       numeric,
    preco_unitario   numeric,
    criterio         text,
    objeto           text,
    classe           text    NOT NULL CHECK (classe IN ('preco_litro', 'gestao', 'nao_unitario', 'indeterminado')),
    motivo_classe    text    NOT NULL,
    pistas_revisao   text[]  NOT NULL DEFAULT '{}',
    numero_controle_pncp text,                    -- preenchido pela conferencia de origem, quando houver
    origem_status    text    NOT NULL DEFAULT 'nao_consultada'
                     CHECK (origem_status IN ('nao_consultada', 'confirmada', 'ausente_no_pncp', 'erro')),
    bruto            jsonb   NOT NULL,
    PRIMARY KEY (lote_id, id_compra_item)
);
CREATE INDEX IF NOT EXISTS registro_ref_idx ON registro (lote_id, classe, uf, data_compra);

CREATE TABLE IF NOT EXISTS avaliacao (
    id               serial PRIMARY KEY,
    lote_id          integer NOT NULL,
    id_compra_item   text    NOT NULL,
    versao_regra     text    NOT NULL,
    grupo            text    NOT NULL,            -- ex.: UF:RJ
    janela_inicio    date    NOT NULL,            -- inclusivo
    janela_fim       date    NOT NULL,            -- inclusivo (dia anterior ao avaliado)
    minimo           integer NOT NULL,
    n                integer NOT NULL,
    q1               numeric,
    mediana          numeric,
    q3               numeric,
    iqr              numeric,
    limite           numeric,
    preco_observado  numeric NOT NULL,
    situacao         text    NOT NULL CHECK (situacao IN ('acima_da_referencia', 'sem_alerta', 'referencia_insuficiente')),
    motivo           text,
    criada_em        timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (lote_id, id_compra_item) REFERENCES registro(lote_id, id_compra_item) ON DELETE CASCADE,
    UNIQUE (lote_id, id_compra_item, versao_regra)
);

CREATE TABLE IF NOT EXISTS avaliacao_comparavel (
    avaliacao_id     integer NOT NULL REFERENCES avaliacao(id) ON DELETE CASCADE,
    lote_id          integer NOT NULL,
    id_compra_item   text    NOT NULL,
    PRIMARY KEY (avaliacao_id, id_compra_item),
    FOREIGN KEY (lote_id, id_compra_item) REFERENCES registro(lote_id, id_compra_item) ON DELETE CASCADE
);

-- v3: varias categorias. O lote diz o que esta sendo comparado e em que unidade;
-- registro.preco_normalizado guarda o preco na unidade de comparacao (R$/L, R$/resma).
ALTER TABLE lote ADD COLUMN IF NOT EXISTS categoria text NOT NULL DEFAULT 'gasolina';
ALTER TABLE lote ADD COLUMN IF NOT EXISTS nome_categoria text NOT NULL DEFAULT 'Gasolina comum';
ALTER TABLE lote ADD COLUMN IF NOT EXISTS unidade_comparacao text NOT NULL DEFAULT 'litro';
ALTER TABLE lote ADD COLUMN IF NOT EXISTS codigo_tipo text NOT NULL DEFAULT 'CATMAT';
ALTER TABLE registro ADD COLUMN IF NOT EXISTS preco_normalizado numeric;
ALTER TABLE registro DROP CONSTRAINT IF EXISTS registro_classe_check;
ALTER TABLE registro ADD CONSTRAINT registro_classe_check CHECK (classe IN
    ('preco_litro', 'preco_resma', 'gestao', 'nao_unitario', 'indeterminado', 'outro_item', 'outra_embalagem'));
