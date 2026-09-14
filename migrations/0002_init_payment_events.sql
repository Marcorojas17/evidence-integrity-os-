-- 🗄️ 0002_init_payment_events.sql
-- ─────────────────────────────────────────────────────────────
-- Eventos crudos de Mercado Pago y resultado de cada verificación.
-- Aquí viven los rechazos de validación. No se crean fulfillments
-- para eventos rechazados.
-- ─────────────────────────────────────────────────────────────

BEGIN;

CREATE TABLE payment_events (
  event_id          BIGSERIAL PRIMARY KEY,
  payment_id        TEXT NOT NULL,
  x_request_id      TEXT NOT NULL,
  order_id          TEXT REFERENCES orders(order_id),
  received_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  processed_at      TIMESTAMPTZ,
  mp_status         TEXT,
  mp_status_detail  TEXT,
  validation_result TEXT NOT NULL DEFAULT 'pending'
                    CHECK (validation_result IN (
                      'pending',
                      'approved_ready',
                      'rejected_not_approved_yet',
                      'rejected_validation',
                      'rejected_signature',
                      'rejected_replay',
                      'rejected_other'
                    )),
  validation_reason TEXT,
  raw_payload       JSONB NOT NULL,
  UNIQUE (payment_id, x_request_id)
);

CREATE INDEX idx_payment_events_payment_id ON payment_events(payment_id);
CREATE INDEX idx_payment_events_order_id   ON payment_events(order_id);
CREATE INDEX idx_payment_events_pending    ON payment_events(received_at)
  WHERE validation_result = 'pending';

COMMIT;
