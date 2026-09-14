# 📝 Changelog

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

### Added
- 🗄️ Migración `0001_init_orders.sql` — tabla de órdenes internas
- 🗄️ Migración `0002_init_payment_events.sql` — eventos crudos de Mercado Pago
- 🗄️ Migración `0003_init_payment_fulfillments.sql` — fulfillment único por pago con lease
- 🗄️ Migración `0004_init_fulfillment_attempts.sql` — tracking de intentos por fulfillment
- 🗄️ Migración `0005_indexes_and_constraints.sql` — triggers de `updated_at` e índices
- 🔒 Núcleo criptográfico: hashing SHA-256, KMS, JCS RFC 8785, manifest v1, JWS RFC 7797, timestamp RFC 3161, hash chain
- 📦 Empaquetado `.evidence`: builder, verifier y CLI
- 💳 Procesador de pagos: firma de webhook, validación de campos, fulfillment con lease, worker de dos fases, recovery, cliente HTTP de Mercado Pago
- ✅ Tests unitarios de hashing, JCS, manifest, JWS, timestamp, hash chain, builder, verifier, CLI, firma, estados, validación y webhook
- 📝 Documentación técnica y legal: `README.md`, `DISCLAIMER.md`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `docs/DATA_PROTECTION.md`, `docs/RETENTION_POLICY.md`, `docs/explanation/legal-mx.md`, `docs/explanation/non-goals.md`, `docs/explanation/threat-model.md`, `docs/reference/algorithm-registry.md`, `docs/tutorials/01-uso-manual.md`
- 📝 ADR 0003 aprobada: `payment_fulfillments`
- 🌐 Landing page con tema claro/oscuro y `prefers-reduced-motion`
- 🔧 Configuración: `pyproject.toml`, `Makefile`, `.gitignore`, `.gitmessage`, `.env.example`
- 🔧 CI con lint, typecheck, tests, seguridad bloqueante y SBOM
- 🔧 Script `scripts/run_migrations.cmd` para Windows

### Pending
- 🌐 API HTTP pública (`/orders`, `/evidence`, `/webhook`, `/verify/{id}`)
- ✅ Tests de integración contra PostgreSQL real
- ✅ Pruebas de concurrencia y recovery end-to-end
- 🧪 Pruebas cruzadas Python ↔ Rust/Node
- 📝 Documentación legal revisada por abogado
- 🔐 Integración con TSA cualificada y proveedor de firma con credenciales reales

---

## [0.0.1] - 2026-09-13

### Added
- 🎉 Estructura inicial del repositorio
- 📝 Definición de arquitectura general
- 📝 Modelo de amenazas preliminar
