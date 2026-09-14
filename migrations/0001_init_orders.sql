-- 🗄️ 0001_init_orders.sql
-- ─────────────────────────────────────────────────────────────
-- Tabla base de órdenes internas. Fuente de verdad del negocio.
-- El external_reference de Mercado Pago apunta a order_id.
-- ─────────────────────────────────────────────────────────────

BEGIN;

CREATE TABLE orders (
  order_id          TEXT PRIMARY KEY,
  user_id           TEXT NOT NULL,
  product_code      TEXT NOT NULL,
  amount            NUMERIC(12,2) NOT NULL CHECK (amount > 0),
  currency          TEXT NOT NULL DEFAULT 'MXN' CHECK (currency ~ '^[A-Z]{3}$'),
  status            TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN (
                      'pending',
                      'processing',
                      'completed',
                      'failed',
                      'failed_requires_manual',
                      'rejected_validation',
                      'cancelled'
                    )),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_orders_user_status ON orders(user_id, status);
CREATE INDEX idx_orders_created_at  ON orders(created_at DESC);

COMMIT;
