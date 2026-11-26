-- Papel somente leitura usado pelo web app (ambiente local).
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'anomaly_leitura') THEN
    CREATE ROLE anomaly_leitura LOGIN PASSWORD 'leitura-local';
  END IF;
END $$;
GRANT CONNECT ON DATABASE anomaly TO anomaly_leitura;
GRANT USAGE ON SCHEMA public TO anomaly_leitura;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anomaly_leitura;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO anomaly_leitura;
