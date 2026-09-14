-- 🗄️ 0003_init_payment_fulfillments.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Un fulfillment por pago aprobado y validado.
-- UNIQUE(payment_id) garantiza emisión única.
-- worker_id + lease_until permiten recovery sin duplicar trabajo.
-- Índices parciales con predicado literal IMMUTABLE (sin now()).
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

CREATE TABLE payment_fulfillments (
  fulfillment_id    BIGSERIAL PRIMARY KEY,
  payment_id        TEXT NOT NULL UNIQUE,
  order_id          TEXT NOT NULL REFERENCES orders(order_id),
  status            TEXT NOT NULL DEFAULT 'queued'
                    CHECK (status IN (
                      'queued',
                      'emitting',
                      'completed',
                      'failed',
                      'abandoned'
                    )),
  worker_id         TEXT,
  lease_until       TIMESTAMPTZ,
  evidence_id       TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_fulfillments_order
  ON payment_fulfillments(order_id);

CREATE INDEX idx_fulfillments_status
  ON payment_fulfillments(status);

-- Recovery: emisiones con lease vencido.
-- Predicado IMMUTABLE; la comparación con now() se hace en query time.
CREATE INDEX idx_fulfillments_emitting_lease
  ON payment_fulfillments(lease_until)
  WHERE status = 'emitting';

-- Recovery: fulfillments en cola que nadie tomó.
CREATE INDEX idx_fulfillments_queued_age
  ON payment_fulfillments(created_at)
  WHERE status = 'queued';

COMMIT;
