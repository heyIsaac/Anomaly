import 'server-only'
import { Pool, types } from 'pg'

// numeric e date chegam como texto: o calculo exato fica no banco e a tela so formata.
types.setTypeParser(1082, (v) => v)

const globalPool = globalThis as unknown as { anomalyPool?: Pool }

export const pool =
  globalPool.anomalyPool ??
  new Pool({
    connectionString:
      process.env.DATABASE_URL_LEITURA ?? 'postgresql://anomaly_leitura:leitura-local@127.0.0.1:5433/anomaly',
    max: 5,
  })

if (process.env.NODE_ENV !== 'production') globalPool.anomalyPool = pool
