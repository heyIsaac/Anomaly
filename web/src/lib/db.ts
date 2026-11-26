import 'server-only'
import { Pool, types } from 'pg'

// numeric e date chegam como texto: o calculo exato fica no banco e a tela so formata.
types.setTypeParser(1082, (v) => v)

const globalPool = globalThis as unknown as { anomalyPool?: Pool }

function urlLeitura() {
  const url = process.env.DATABASE_URL_LEITURA
  if (url) return url
  // Na Vercel nao existe banco local: falhar com motivo claro em vez de tentar 127.0.0.1.
  if (process.env.VERCEL) {
    throw new Error(`DATABASE_URL_LEITURA nao definida para o ambiente "${process.env.VERCEL_ENV}" na Vercel`)
  }
  return 'postgresql://anomaly_leitura:leitura-local@127.0.0.1:5433/anomaly'
}

export const pool =
  globalPool.anomalyPool ??
  new Pool({
    connectionString: urlLeitura(),
    max: 5,
  })

if (process.env.NODE_ENV !== 'production') globalPool.anomalyPool = pool
