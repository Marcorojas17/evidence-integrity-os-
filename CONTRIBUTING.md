# 🤝 Guía de Contribución

Gracias por tu interés en Evidence Integrity OS.

---

## 📋 Antes de empezar

1. Lee el [`README.md`](README.md) para entender el alcance del sistema.
2. Revisa [`DISCLAIMER.md`](DISCLAIMER.md) para conocer los límites.
3. Consulta [`SECURITY.md`](SECURITY.md) si encuentras una vulnerabilidad.

## 🎯 Áreas de contribución

- Criptografía aplicada (JCS, JWS, RFC 3161, PAdES)
- Seguridad de procesadores de pago e idempotencia
- Interoperabilidad entre implementaciones (Python ↔ Rust/Node)
- Privacidad y minimización de datos (LFPDPPP)
- Documentación técnica y legal
- Pruebas reproducibles

## 🚫 Lo que no se acepta

- Evidencia real o datos personales en ejemplos, tests o issues.
- Secretos, tokens, certificados privados o claves en el repositorio.
- Afirmaciones de cumplimiento normativo, certificación o admisibilidad judicial.
- Cambios en el formato `manifest.payload.json` sin proponer una ADR.
- Cambios en la arquitectura de pagos sin actualizar la documentación.

## 🔧 Flujo de trabajo

1. **Fork** del repositorio.
2. Crea una rama descriptiva: `feat/`, `fix/`, `docs/`, `refactor/`.
3. Commits siguiendo [Conventional Commits](https://www.conventionalcommits.org/) + Gitmoji.
4. Abre un Pull Request describiendo qué, por qué y cómo se probó.

## 📝 Convención de commits (Gitmoji)

| Emoji | Uso |
|-------|-----|
| 🗄️ | Migración SQL |
| ✨ | Nueva funcionalidad |
| 🐛 | Corrección de bug |
| 🔒 | Seguridad / criptografía |
| 📝 | Documentación |
| ✅ | Tests |
| ♻️ | Refactor |
| 🚀 | Release |
| 🔧 | Configuración |
| 💥 | Breaking change |
| 🩹 | Fix menor |
| 🧪 | Fixtures / pruebas |
| 📦 | Paquete `.evidence` |
| 🔑 | Claves / KMS |
| ⛓️ | Hash chain / anclaje |
| 💳 | Pagos |

## 🧪 Pruebas

| Tipo | Ubicación |
|------|-----------|
| Unitarias | `tests/unit/` |
| Integración | `tests/integration/` |
| Seguridad | `tests/security/` |
| Reproducibilidad | `tests/reproducibility/` |

## 📐 Decisiones arquitectónicas

Si tu cambio afecta formato, estructura o algoritmos, abre una **ADR** en `docs/adr/`.

---

Al enviar un Pull Request aceptas que tu contribución se publique bajo la licencia MIT (código) o CC-BY-4.0 (documentación).
