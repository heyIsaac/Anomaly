import 'server-only'
import { pool } from './db'

export type Situacao = 'acima_da_referencia' | 'sem_alerta' | 'referencia_insuficiente'
export type OrigemStatus = 'confirmada' | 'ausente_no_pncp' | 'nao_consultada' | 'erro'

export type Lote = {
  id: number
  categoria: string
  nome_categoria: string
  unidade_comparacao: string
  codigo_tipo: string
  fonte: string
  catmat: number
  extraido_em: string
  carregado_em: Date
  total_unico: number
  versao_classificacao: string
  classes: Record<string, number>
}

export type Ocorrencia = {
  id_compra_item: string
  data_compra: string
  municipio: string
  nome_orgao: string
  preco_observado: string
  limite: string | null
  situacao: Situacao
}

export type Detalhe = Ocorrencia & {
  avaliacao_id: number
  lote_id: number
  catmat: number
  unidade: string | null
  preco_unitario: string
  capacidade: number | null
  id_compra: string
  codigo_uasg: string
  numero_item: number | null
  uf: string
  quantidade: string
  objeto: string
  criterio: string | null
  pistas_revisao: string[]
  origem_status: OrigemStatus
  numero_controle_pncp: string | null
  versao_regra: string
  grupo: string
  janela_inicio: string
  janela_fim: string
  minimo: number
  n: number
  q1: string | null
  mediana: string | null
  q3: string | null
  iqr: string | null
  motivo: string | null
}

export type Comparavel = {
  id_compra_item: string
  data_compra: string
  municipio: string
  nome_orgao: string
  preco_unitario: string
}

const LOTE_COLS = `l.id, l.categoria, l.nome_categoria, l.unidade_comparacao, l.codigo_tipo, l.fonte, l.catmat,
  l.extraido_em, l.carregado_em, l.total_unico, l.versao_classificacao,
  (SELECT json_object_agg(classe, n) FROM (SELECT classe, count(*)::int n FROM registro
    WHERE lote_id = l.id GROUP BY classe) c) AS classes`

/** Lote mais recente de cada categoria que ja tem avaliacoes, na ordem em que a categoria apareceu. */
export async function lotesAtuais(): Promise<Lote[]> {
  const { rows } = await pool.query(
    `SELECT ${LOTE_COLS} FROM lote l
      WHERE l.id IN (SELECT max(id) FROM lote x WHERE EXISTS (SELECT 1 FROM avaliacao a WHERE a.lote_id = x.id)
                      GROUP BY categoria)
      ORDER BY (SELECT min(id) FROM lote y WHERE y.categoria = l.categoria)`,
  )
  return rows
}

export async function loteDe(id: number): Promise<Lote | null> {
  const { rows } = await pool.query(`SELECT ${LOTE_COLS} FROM lote l WHERE l.id = $1`, [id])
  return rows[0] ?? null
}

export async function contagens(lote: number): Promise<Record<Situacao, number>> {
  const { rows } = await pool.query(
    'SELECT situacao, count(*)::int n FROM avaliacao WHERE lote_id = $1 GROUP BY situacao',
    [lote],
  )
  const out = { acima_da_referencia: 0, sem_alerta: 0, referencia_insuficiente: 0 }
  for (const r of rows) out[r.situacao as Situacao] = r.n
  return out
}

export async function municipios(lote: number): Promise<string[]> {
  const { rows } = await pool.query(
    `SELECT DISTINCT r.municipio FROM avaliacao a JOIN registro r USING (lote_id, id_compra_item)
      WHERE a.lote_id = $1 ORDER BY 1`,
    [lote],
  )
  return rows.map((r) => r.municipio)
}

export async function ocorrencias(lote: number, situacao: Situacao | null, municipio: string | null) {
  const { rows } = await pool.query<Ocorrencia>(
    `SELECT a.id_compra_item, r.data_compra, r.municipio, r.nome_orgao, a.preco_observado, a.limite, a.situacao
       FROM avaliacao a JOIN registro r USING (lote_id, id_compra_item)
      WHERE a.lote_id = $1 AND ($2::text IS NULL OR a.situacao = $2) AND ($3::text IS NULL OR r.municipio = $3)
      ORDER BY (a.situacao = 'acima_da_referencia') DESC, r.data_compra DESC, a.id_compra_item`,
    [lote, situacao, municipio],
  )
  return rows
}

export async function detalhe(lotes: number[], id: string): Promise<Detalhe | null> {
  const { rows } = await pool.query<Detalhe>(
    `SELECT a.id AS avaliacao_id, a.lote_id, r.catmat, r.unidade, r.preco_unitario,
            (r.bruto->>'capacidadeUnidadeFornecimento')::numeric::int AS capacidade, a.id_compra_item, r.id_compra, r.codigo_uasg, (r.bruto->>'numeroItemCompra')::int AS numero_item,
            r.data_compra, r.uf, r.municipio, r.nome_orgao, r.quantidade, r.objeto, r.criterio, r.pistas_revisao,
            r.origem_status, r.numero_controle_pncp, a.versao_regra, a.grupo, a.janela_inicio, a.janela_fim, a.minimo,
            a.n, a.q1, a.mediana, a.q3, a.iqr, a.limite, a.preco_observado, a.situacao, a.motivo
       FROM avaliacao a JOIN registro r USING (lote_id, id_compra_item)
      WHERE a.lote_id = ANY($1::int[]) AND a.id_compra_item = $2
      ORDER BY a.lote_id DESC LIMIT 1`,
    [lotes, id],
  )
  return rows[0] ?? null
}

export async function comparaveis(avaliacaoId: number) {
  const { rows } = await pool.query<Comparavel>(
    `SELECT r.id_compra_item, r.data_compra, r.municipio, r.nome_orgao,
            COALESCE(r.preco_normalizado, r.preco_unitario) AS preco_unitario
       FROM avaliacao_comparavel c JOIN registro r ON r.lote_id = c.lote_id AND r.id_compra_item = c.id_compra_item
      WHERE c.avaliacao_id = $1 ORDER BY 5 DESC, r.data_compra DESC`,
    [avaliacaoId],
  )
  return rows
}
