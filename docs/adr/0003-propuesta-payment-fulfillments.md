# ADR 0003: Tabla payment_fulfillments

## Estado

Aprobada. Implementada en `migrations/0003_init_payment_fulfillments.sql`.
Complementada por `migrations/0004_init_fulfillment_attempts.sql`.

## Contexto

El procesador de pagos necesita garantizar que un pago aprobado genere
exactamente una emisión de evidencia, incluso bajo concurrencia y
reintentos. Se necesita una entidad que actúe como garantía de
idempotencia a nivel de negocio.

## Decisión

Crear una tabla `payment_fulfillments` con:

- `payment_id` único.
- Estados: `queued`, `emitting`, `completed`, `failed`, `abandoned`.
- `worker_id` y `lease_until` para recuperación sin duplicar trabajo.
- Índices parciales con predicados de estado (literales, sin `now()`).
- Registro de cada intento en `fulfillment_attempts` (migración 0004).

## Modelo de dos fases

**FASE A — Validación**
- No abre transacción.
- Consulta `GET /v1/payments/{id}`.
- Valida campos: status, monto, moneda, external_reference, collector_id,
  preference_id, live_mode, ausencia de reembolso.
- No crea fulfillment si el pago no está aprobado.

**FASE B — Fulfillment**
- Transacción corta para `INSERT ... ON CONFLICT DO NOTHING`.
- Si no retorna fila, otro worker ya reclamó.
- `worker_id` y `lease_until` permiten recuperación sin duplicar.
- Emisión fuera de transacción; lease renovado periódicamente.
- Cierre en transacción corta que actualiza fulfillment, attempt y orden.

## Modelo de recovery

- Solo se recuperan fulfillments con `lease_until < now()` en estado
  `emitting`, o `created_at < now() - 10 min` en estado `queued`.
- `UPDATE` condicional con predicado reemplaza `SELECT ... FOR UPDATE`
  prolongado.
- Nuevo intento con `trigger='recovery_after_crash'`.

## Pendientes

- Pruebas de integración con PostgreSQL real (concurrencia, recovery).
- Pruebas de idempotencia con webhooks duplicados.
- Revisión con asesoría legal el tratamiento de hashes y datos personales
  en la tabla.

## Criterios de aceptación

- La migración aplica sin errores en base limpia.
- Los tests de concurrencia no duplican emisiones.
- Los tests de recovery no re-emiten fulfillments completados.
- El planner usa los índices parciales en las consultas esperadas.

## Consecuencias

Aplicadas:
- Se añadió `migrations/0003_init_payment_fulfillments.sql`.
- Se actualizó `CHANGELOG.md`.
- Se creó `migrations/0004_init_fulfillment_attempts.sql`.
- Se implementó el flujo en `src/payments/fulfillment.py`.

## Referencias

- Arquitectura de pagos en dos fases.
- RFC 3161, RFC 8785, RFC 7797.
- Discusión previa sobre idempotencia y concurrencia.
- `src/payments/fulfillment.py`, `src/payments/recovery.py`.
