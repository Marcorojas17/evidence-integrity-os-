-- 🗄️ 0004_init_fulfillment_attempts.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Un intento por ejecución de emisión sobre un mismo fulfillment.
-- Registra webhook, reintentos automáticos, recuperación tras caída y
-- acciones manuales del operador, sin duplicar el fulfillment.
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

CREATE TABLE fulfillment_attempts (
  attempt_id        BIGSERIAL PRIMARY KEY,
  fulfillment_id    BIGINT NOT NULL
                    REFERENCES payment_fulfillments(fulfillment_id)
                    ON DELETE CASCADE,
  attempt_number    INT NOT NULL CHECK (attempt_number >= 1),
  trigger           TEXT NOT NULL
                    CHECK (trigger IN (
                      'webhook',
                      'manual_operator',
                      'retry_scheduled',
                      'recovery_after_crash'
                    )),
  worker_id         TEXT,
  started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at       TIMESTAMPTZ,
  result            TEXT
                    CHECK (result IS NULL OR result IN (
                      'success',
                      'failed_retryable',
                      'failed_permanent',
                      'aborted_conflict',
                      'aborted_crash'
                    )),
  error_detail      TEXT,
  UNIQUE (fulfillment_id, attempt_number)
);

CREATE INDEX idx_attempts_fulfillment
  ON fulfillment_attempts(fulfillment_id);

-- Intentos sin terminar: candidatos a diagnóstico y recovery.
CREATE INDEX idx_attempts_open
  ON fulfillment_attempts(started_at)
  WHERE finished_at IS NULL;

-- Búsquedas por worker para auditoría operativa.
CREATE INDEX idx_attempts_worker
  ON fulfillment_attempts(worker_id)
  WHERE worker_id IS NOT NULL;

COMMIT;
