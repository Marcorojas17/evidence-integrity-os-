# 🤝 Guía de Contribución

> [!IMPORTANT]
> **Contribuciones externas no aceptadas en la fase actual.**
>
> El proyecto se encuentra en etapa de diseño y no cuenta con:
>
> - Canal de moderación formalizado
> - Equipo de revisión asignado
> - Niveles de servicio comprometidos
>
> Esta guía describe el proceso que aplicará una vez que el canal de moderación y el equipo de revisión estén activos.

---

## 📋 Estado actual

No se reciben Pull Requests, issues de propuesta ni discusiones abiertas al público general.

Excepciones:

- Reportes de vulnerabilidades técnicas: ver [`SECURITY.md`](SECURITY.md).
- Reportes de conducta: ver [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) para el estado del canal de moderación.

## 🎯 Áreas previstas para contribución futura

- Criptografía aplicada (JCS, JWS, RFC 3161, PAdES)
- Seguridad de procesadores de pago e idempotencia
- Interoperabilidad Python ↔ Rust/Node
- Privacidad y minimización de datos
- Documentación técnica y legal
- Pruebas reproducibles

## 🚫 Lo que no se aceptará

- Evidencia real o datos personales en ejemplos, tests o issues.
- Secretos, tokens, certificados privados o claves.
- Afirmaciones de cumplimiento normativo, certificación o admisibilidad.
- Cambios en `manifest.payload.json` sin ADR.
- Cambios en la arquitectura de pagos sin actualizar la documentación.

## 🔧 Flujo previsto (cuando se abra)

1. Fork del repositorio.
2. Rama descriptiva: `feat/`, `fix/`, `docs/`, `refactor/`.
3. Commits con Conventional Commits + Gitmoji.
4. Pull Request describiendo qué, por qué y cómo se probó.

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

## 📐 Decisiones arquitectónicas

Cambios que afecten formato, estructura o algoritmos requerirán una **ADR** en `docs/adr/` antes de implementarse.

## 📅 Cuándo se abrirán las contribuciones

Cuando estén operativos:

1. Canal de moderación de conducta.
2. Equipo de revisión de Pull Requests.
3. Niveles de respuesta documentados.
4. Política de aceptación publicada.

Hasta entonces, esta guía se considera informativa.
