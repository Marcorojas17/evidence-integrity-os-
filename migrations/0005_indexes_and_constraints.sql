-- 🗄️ 0005_indexes_and_constraints.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Triggers de updated_at e indices transversales.
-- Sin reglas de negocio aquí: solo consistencia temporal y performance.
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

-- ─── Trigger genérico de updated_at ─────────────────────────────────────────

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_orders_updated_at
  BEFORE UPDATE ON orders
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_fulfillments_updated_at
  BEFORE UPDATE ON payment_fulfillments
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ─── Índices para consultas del worker ──────────────────────────────────────

-- Buscar eventos pendientes de validacion.
-- El indice parcial ya existe (idx_payment_events_pending) en 0002.

-- Órdenes por estado, para listados administrativos.
CREATE INDEX idx_orders_status
  ON orders(status);

-- Eventos de un pago, ordenados por recepción.
CREATE INDEX idx_payment_events_received
  ON payment_events(payment_id, received_at DESC);

-- ─── Verificaciones de integridad referencial ───────────────────────────────

-- Cada fulfillment debe tener al menos un attempt (se valida en aplicación,
-- no en trigger, para no bloquear inserciones transitorias).

COMMIT;
