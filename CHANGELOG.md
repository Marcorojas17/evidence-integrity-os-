```text
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   ██████╗██╗  ██╗ █████╗ ███╗   ██╗ ██████╗ ███████╗██╗      ██████╗      ║
║  ██╔════╝██║  ██║██╔══██╗████╗  ██║██╔════╝ ██╔════╝██║     ██╔═══██╗     ║
║  ██║     ███████║███████║██╔██╗ ██║██║  ███╗█████╗  ██║     ██║   ██║     ║
║  ██║     ██╔══██║██╔══██║██║╚██╗██║██║   ██║██╔══╝  ██║     ██║   ██║     ║
║  ╚██████╗██║  ██║██║  ██║██║ ╚████║╚██████╔╝███████╗███████╗╚██████╔╝     ║
║   ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚══════╝ ╚═════╝      ║
║                                                                          ║
║   EVIDENCE INTEGRITY OS :: registro de cambios                          ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
```

![Version](https://img.shields.io/badge/version-0.0.1-00ff41?style=for-the-badge&labelColor=0a0d10)
![Estado](https://img.shields.io/badge/estado-pre--alpha-ffcc00?style=for-the-badge&labelColor=0a0d10)
![Formato](https://img.shields.io/badge/formato-keep%20a%20changelog-00ffff?style=for-the-badge&labelColor=0a0d10)
![Semver](https://img.shields.io/badge/semver-2.0.0-ff00ff?style=for-the-badge&labelColor=0a0d10)

```text
> Todos los cambios notables de este proyecto son documentados en este archivo.
> El formato sigue Keep a Changelog 1.1.0.
> El proyecto adhiere a Semantic Versioning 2.0.0.
```

---

```text
┌─[ UNRELEASED ]───────────────────────────────────────────────────── desarrollo ─┐
│                                                                                │
│  Rama activa. Sin release todavía. Todos los cambios se acumulan aquí          │
│  hasta el primer tag estable.                                                  │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

### `+++ AÑADIDO`

```text
  [🗄️]  BASE DE DATOS
```

- 🗄️ Migración `0001_init_orders.sql` — tabla de órdenes internas
- 🗄️ Migración `0002_init_payment_events.sql` — eventos crudos de Mercado Pago
- 🗄️ Migración `0003_init_payment_fulfillments.sql` — fulfillment único por pago con lease
- 🗄️ Migración `0004_init_fulfillment_attempts.sql` — tracking de intentos por fulfillment
- 🗄️ Migración `0005_indexes_and_constraints.sql` — triggers de `updated_at` e índices

```text
  [🔒]  NÚCLEO CRIPTOGRÁFICO
```

- 🔒 Hashing SHA-256 y compromiso HMAC delegado a KMS
- 🔒 Interfaz KMS: `LocalKMS`, stubs `AWSKMS` y `VaultKMS`
- 🔒 Canonicalización JCS RFC 8785 vía `rfc8785`
- 🔒 Manifiesto v1 con validación contra JSON Schema
- 🔒 JWS detached RFC 7797 con allowlist y rechazo de `alg=none`
- 🔒 Cliente RFC 3161 con verificación de `messageImprint`
- 🔒 Hash chain con detección de alteración, reordenamiento y bifurcación

```text
  [⛓️]  LOG DE AUDITORÍA
```

- ⛓️ Logger encadenado con firma por evento
- ⛓️ Anclaje externo: `LocalFilesystemAnchor`, stubs de S3 Object Lock y Azure Immutable Blob
- ⛓️ Cierres firmados y verificables del log completo
- ⛓️ Verificación end-to-end: cadena, firmas, cierres y anclajes

```text
  [📦]  EMPAQUETADO .EVIDENCE
```

- 📦 Builder del paquete `.evidence` con manifest, JWS, token, firmas y README
- 📦 Verifier end-to-end con resultado estructurado
- 📦 CLI `evidence-verify` con salida legible y modo `--json`

```text
  [💳]  PROCESADOR DE PAGOS
```

- 💳 Firma de webhook de Mercado Pago con comparación constant-time
- 💳 Ventana temporal de 5 minutos y rechazo de replay
- 💳 Soporte de múltiples valores `v1` durante rotación de secretos
- 💳 Validación de campos del pago contra la orden (monto, moneda, collector, preference, live_mode)
- 💳 Fulfillment único por pago con lease renovable
- 💳 Worker con flujo de dos fases: validación sin transacción, emisión con transacciones cortas
- 💳 Recovery de fulfillments huérfanos con `lease_until < now()`
- 💳 Cliente HTTP de Mercado Pago con `X-Idempotency-Key`

```text
  [🌐]  API HTTP
```

- 🌐 App FastAPI con routers de órdenes, evidencia, webhook, público y admin
- 🌐 Middleware de `x-request-id` y audit log básico
- 🌐 Endpoint `/health` para probes
- 🌐 Verificación pública con divulgación mínima
- 🌐 Endpoints administrativos con autenticación por token

```text
  [✅]  TESTS
```

- ✅ Unitarios de hashing, JCS, manifest, JWS, timestamp, hash chain
- ✅ Unitarios de builder, verifier y CLI
- ✅ Unitarios de firma, estados, validación y webhook
- ✅ Unitarios de log encadenado y verificación de integridad
- ✅ Seguridad: confusión de algoritmos, ataques de diccionario, corrupción, validación de esquema

```text
  [📝]  DOCUMENTACIÓN
```

- 📝 `README.md` — guía general, límites legales, arquitectura
- 📝 `DISCLAIMER.md` — aviso legal explícito
- 📝 `SECURITY.md` — política de seguridad sin correo personal
- 📝 `CONTRIBUTING.md` — guía de contribución (cerrada en fase actual)
- 📝 `CODE_OF_CONDUCT.md` — código de conducta
- 📝 `docs/DATA_PROTECTION.md` — protección de datos y hashes como dato personal
- 📝 `docs/RETENTION_POLICY.md` — política de retención con logs condicionados
- 📝 `docs/explanation/legal-mx.md` — marco legal mexicano como alineación de diseño
- 📝 `docs/explanation/non-goals.md` — no-objetivos del sistema
- 📝 `docs/explanation/threat-model.md` — modelo STRIDE
- 📝 `docs/reference/algorithm-registry.md` — registro de algoritmos
- 📝 `docs/tutorials/01-uso-manual.md` — tutorial sin terminal
- 📝 `docs/adr/0003-propuesta-payment-fulfillments.md` — ADR aprobada

```text
  [🔧]  CONFIGURACIÓN Y HERRAMIENTAS
```

- 🔧 `pyproject.toml` con dependencias, entry point y configuración de ruff, mypy, pytest, coverage, bandit
- 🔧 `Makefile` con tareas de desarrollo, migraciones y Docker
- 🔧 `.gitignore`, `.gitmessage`, `.env.example`
- 🔧 `.github/workflows/ci.yml` con lint, typecheck, tests, seguridad bloqueante y SBOM
- 🔧 `scripts/run_migrations.cmd` para Windows
- 🔧 `scripts/demo_build_verify.cmd` para demo end-to-end

```text
  [🌐]  LANDING
```

- 🌐 `index.html` con tema claro/oscuro, persistencia y `prefers-reduced-motion`
- 🌐 Red de nodos animada en canvas
- 🌐 Toggle de tema con iconos sun/moon

### `~~~ PENDIENTE`

```text
  [ ]  Tests de integración contra PostgreSQL real
  [ ]  Pruebas de concurrencia y recovery end-to-end
  [ ]  Pruebas cruzadas Python ↔ Rust/Node
  [ ]  Implementación real de AWSKMS
  [ ]  Implementación real de S3ObjectLockAnchor
  [ ]  Integración con TSA cualificada y proveedor de firma
  [ ]  Revisión legal, de privacidad y seguridad externa
```

---

```text
┌─[ 0.0.1 ]─────────────────────────────────────────────────────── 2026-09-13 ─┐
│                                                                             │
│  Release inicial. Estructura del repositorio, arquitectura y documentación  │
│  fundacional.                                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### `+++ AÑADIDO`

- 🎉 Estructura inicial del repositorio
- 📝 Definición de arquitectura general
- 📝 Modelo de amenazas preliminar
- 📝 Manifiesto v1 congelado
- 📝 Especificación de JWS detached
- 📝 Arquitectura de pagos con flujo de dos fases

---

```text
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   [ EVIDENCE INTEGRITY OS ]                                              ║
║                                                                          ║
║   Integridad verificable.                                                ║
║   Trazabilidad responsable.                                              ║
║   Sin promesas jurídicas automáticas.                                    ║
║                                                                          ║
║   root@evidence:~# tail -f CHANGELOG.md                                  ║
║   █                                                                      ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
```
