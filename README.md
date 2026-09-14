```text
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   ███████╗██╗   ██╗██╗██████╗ ███████╗███╗   ██╗ ██████╗███████╗         ║
║   ██╔════╝██║   ██║██║██╔══██╗██╔════╝████╗  ██║██╔════╝██╔════╝         ║
║   █████╗  ██║   ██║██║██║  ██║█████╗  ██╔██╗ ██║██║     █████╗           ║
║   ██╔══╝  ╚██╗ ██╔╝██║██║  ██║██╔══╝  ██║╚██╗██║██║     ██╔══╝           ║
║   ███████╗ ╚████╔╝ ██║██████╔╝███████╗██║ ╚████║╚██████╗███████╗         ║
║   ╚══════╝  ╚═══╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝╚══════╝         ║
║                                                                          ║
║   I N T E G R I T Y   O S   ::   v0.0.1                                  ║
║   cadena de custodia digital verificable                                 ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
```

**Plataforma de integridad, trazabilidad y verificación de evidencia digital para México y Latinoamérica.**

```text
[ HASH ]  SHA-256 + HMAC          [ TIME ]  RFC 3161
[ PROOF ] .evidence               [ AUDIT ] Hash Chain
[ FORM  ] JCS RFC 8785            [ SIGN  ] JWS RFC 7797
```

![Estado](https://img.shields.io/badge/estado-en%20dise%C3%B1o-00e5ff?style=for-the-badge&logo=github&logoColor=white)
![Núcleo](https://img.shields.io/badge/n%C3%BAcleo%20criptogr%C3%A1fico-completo-10b981?style=for-the-badge)
![Código](https://img.shields.io/badge/licencia-MIT%20%2B%20CC--BY--4.0-8b5cf6?style=for-the-badge)

```text
> WARNING: Evidence Integrity OS no sustituye a abogado, perito, notario
> ni Prestador de Servicios de Certificación (PSC). Los sellos RFC 3161 y
> las constancias NOM-151 son emitidos exclusivamente por terceros
> autorizados.
```

---

```text
┌─[ 01 ]───────────────────────────────────────────────────────────── MISIÓN ─┐
│                                                                             │
│  Preservar evidencia digital de forma verificable, trazable y               │
│  exportable, minimizando la necesidad de confiar ciegamente en una          │
│  sola plataforma.                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

```text
ARCHIVO ORIGINAL
       │
       ├──▶ content_hash       (SHA-256, verificable por terceros)
       ├──▶ private_commitment (HMAC-SHA256 vía KMS, prueba privada)
       ├──▶ token.rfc3161      (TSA externa, vinculado al hash)
       ├──▶ evidence-report.pdf (PAdES-B-T: firma + sello de tiempo)
       └──▶ evento encadenado + anclaje externo
       │
       ▼
PAQUETE .evidence VERIFICABLE
```

---

```text
┌─[ 02 ]───────────────────────────────────────────────────────── QUÉ HACE ─┐
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

| Módulo | Función |
|--------|---------|
| 📦 **Paquete `.evidence`** | Convierte archivos en paquetes verificables e independientes. |
| 🔒 **Integridad** | Calcula `content_hash` (SHA-256) y `private_commitment` (HMAC, prueba privada). |
| 🕐 **Tiempo** | Integra sellos RFC 3161 emitidos por una TSA externa. |
| 📄 **Reporte** | Genera `evidence-report.pdf` con firma PAdES-B-T (firma + sello de tiempo). |
| ⛓️ **Auditoría** | Registra eventos en una hash chain con anclaje externo. |
| 🌐 **Verificación** | Ofrece consulta pública mínima, solo con consentimiento explícito. |
| 💳 **Pagos** | Gestiona órdenes, webhooks e idempotencia para la emisión. |

---

```text
┌─[ 03 ]────────────────────────────────────────────────────── LÍMITES ─┐
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

| ✅ ESTE SISTEMA SÍ | ❌ ESTE SISTEMA NO |
|--------------------|--------------------|
| Vincula un hash con una fecha/hora verificable mediante token RFC 3161 emitido por una TSA externa. | No certifica autoría, titularidad ni veracidad del contenido. |
| Conserva artefactos criptográficos para revisión independiente. | No emite constancias NOM-151 (solo un PSC acreditado puede hacerlo). |
| Mantiene trazabilidad operativa y eventos auditables. | No garantiza la admisibilidad judicial de una prueba. |
| Facilita verificación técnica reproducible por terceros. | No sustituye asesoría jurídica, pericial o notarial. |

```text
> CAUTION: La valoración de una evidencia depende del contexto, la cadena
> de custodia, la normativa aplicable y la autoridad competente.
```

---

```text
┌─[ 04 ]───────────────────────────────────── CONTENIDO DEL PAQUETE ─┐
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

```text
paquete.evidence
├── manifest.payload.json       ← Metadatos y hashes canónicos (JCS, RFC 8785)
├── manifest.jws.json           ← Firma JWS detached (RFC 7797, b64=false)
├── token.rfc3161               ← Sello de tiempo RFC 3161 (ASN.1 DER)
├── evidence-report.pdf         ← Reporte técnico PAdES-B-T
├── proofs/
│   ├── chain_<position>.json   ← Entrada de hash chain
│   └── anchor_<position>.json  ← Anclaje externo (opcional)
├── signatures/
│   ├── signing_cert.pem        ← Certificado de firma
│   └── ca_chain.pem            ← Cadena de confianza
├── original/                   ← OPCIONAL, desactivado en MVP
└── README.txt                  ← Instrucciones de verificación
```

```text
> NOTA: El archivo original NO se incluye por defecto. El MVP lo desactiva.
> Verificar la estructura, firmas y sellos NO requiere el original.
> Comparar un archivo específico contra el paquete SÍ requiere recalcular
> su content_hash.
```

### Perfiles PAdES

```text
  PAdES-B-B    ──▶  firma sin sello de tiempo
  PAdES-B-T    ──▶  firma + sello RFC 3161              ◀── MVP
  PAdES-B-LT   ──▶  B-T + OCSP/CRL embebidos en el PDF
  PAdES-B-LTA  ──▶  B-LT + sellos de archivo periódicos
```

Un `ocsp.der` en `proofs/` **no convierte** el PDF en B-LT. El material de validación debe embeberse en el PDF según ETSI EN 319 142-1.

---

```text
┌─[ 05 ]────────────────────────────────── ARQUITECTURA DE CONFIANZA ─┐
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

```mermaid
flowchart LR
    A[Archivo original] --> B[content_hash SHA-256]
    A --> C[private_commitment HMAC]
    B --> D[manifest.payload.json JCS]
    D --> E[manifest.jws.json]
    B --> F[token.rfc3161]
    D --> G[Paquete .evidence]
    E --> G
    F --> G
    G --> H[Evento de auditoría]
    H --> I[Hash chain]
    I --> J[Anclaje externo]
    G --> K[Verificación independiente]
```

### Naturaleza de las pruebas

| Elemento | Naturaleza | Verificable por |
|----------|-----------|-----------------|
| `content_hash` (SHA-256) | Prueba pública e interoperable | Cualquiera con el archivo original |
| `private_commitment` (HMAC) | Prueba privada controlada por el sistema | Solo el sistema/titular autorizado |
| `token.rfc3161` | Vinculación temporal emitida por TSA externa | Cualquiera con el token |
| `manifest.jws.json` | Firma de integridad del manifiesto | Cualquiera con la clave pública |
| `evidence-report.pdf` | Reporte técnico con firma PAdES-B-T | Cualquiera con Adobe Reader o equivalente |

```text
> SOBRE EL HMAC: private_commitment es una prueba privada que aporta
> control adicional del titular. NO protege al content_hash público
> contra ataques de diccionario. Si el archivo tiene baja entropía, el
> content_hash público sigue siendo comprobable por terceros mediante
> diccionario.
```

---

```text
┌─[ 06 ]─────────────────────────────────────── MARCO DE REFERENCIA ─┐
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Alineación de diseño con normativa mexicana

```text
> "Alineación de diseño" significa que el sistema se construye considerando
> estas normas. NO implica cumplimiento certificado, ni admisibilidad
> automática, ni respaldo oficial.
```

| Norma | Materia |
|-------|---------|
| **NOM-151-SCFI-2016** (DOF 30/03/2017) | Conservación de mensajes de datos. Constancia emitida por PSC acreditado. |
| **Código de Comercio, Art. 97** | Uso de firma electrónica en mensajes de datos. |
| **CNPP, Art. 265** | Valoración de datos y pruebas. |
| **LFPDPPP** | Protección de datos personales en posesión de particulares. |

### Estándares internacionales

```text
  RFC 3161              ──▶  Time-Stamp Protocol (TSP)
  RFC 8785              ──▶  JSON Canonicalization Scheme (JCS)
  RFC 7797              ──▶  JWS Unencoded Payload Option
  RFC 7515 / 7518 / 7638 ──▶  JWS, algoritmos, thumbprints
  ETSI EN 319 142-1     ──▶  Perfiles PAdES
  ISO/IEC 27001         ──▶  Gestión de seguridad (referencia)
  ISO/IEC 27037         ──▶  Guía forense digital (referencia)
```

```text
> Ninguna de estas referencias implica certificación. Solo describen el
> marco técnico sobre el cual se diseña el sistema.
```

---

```text
┌─[ 07 ]─────────────────────────────────────── ESTADO DEL PROYECTO ─┐
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

| Componente | Estado |
|------------|--------|
| Núcleo criptográfico | ✅ hashing, KMS, JCS, manifest, JWS, timestamp, hash_chain |
| Empaquetado `.evidence` | ✅ builder + verifier + CLI |
| Migraciones SQL | 🔄 2/5 aprobadas (0001, 0002) |
| Procesador de pagos | ⬜ Pendiente |
| API HTTP | ⬜ Pendiente |
| UI | ✅ Landing estática con tema claro/oscuro |
| Revisión legal México | ⚠️ Bloqueante externo |

### Barra de progreso

```text
  Núcleo criptográfico  ████████████████████████████████████ 100%
  Empaquetado .evidence ████████████████████████████████████ 100%
  Migraciones SQL       ████████████░░░░░░░░░░░░░░░░░░░░░░░░  40%
  Procesador de pagos   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   0%
  API HTTP              ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   0%
  UI (landing)          ████████████████████████████████████ 100%
  Revisión legal MX     ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   0%
```

---

```text
┌─[ 08 ]──────────────────────────────────────────────────────────── DEMO ─┐
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

```text
> DESPLIEGUE PENDIENTE. La landing pública se activará cuando el
> repositorio complete su revisión técnica y legal.
```

### Cómo verificar un paquete manualmente

```bash
$ pip install -e ".[dev]"
$ evidence-verify --package caso.evidence
```

Salida esperada:

```text
[1/7] estructura ... ok
[2/7] manifest.canonical ... ok
[3/7] manifest.schema ... ok
[4/7] jws ... ok (firma valida)
[5/7] rfc3161.imprint ... ok
[6/7] hash_chain ... ok
[7/7] operational ... ok (revocacion: active)

-> RESULTADO: VALIDO
   evidence_id: ev_abc12345
   manifest_digest: 9ca381f5...
   tsa_gen_time: 2026-09-13T12:00:02+00:00
   revocacion: active
```

---

```text
┌─[ 09 ]───────────────────────────────────────── SEGURIDAD Y PRIVACIDAD ─┐
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

Si detectas una vulnerabilidad, **no publiques detalles sensibles en un issue público**. Consulta [`SECURITY.md`](SECURITY.md) para el canal de reporte responsable.

```text
  Minimización de datos        ·   Control de acceso por rol
  Cifrado en tránsito          ·   Registro de accesos y operaciones
  Políticas de retención       ·   Revisión con especialistas LFPDPPP
```

---

```text
┌─[ 10 ]────────────────────────────────────────────────────── HOJA DE RUTA ─┐
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

- [x] Definir `manifest.payload.json` v1.
- [x] Documentar límites legales y no-objetivos.
- [x] Congelar arquitectura de pagos.
- [x] Implementar núcleo criptográfico (hashing, JCS, JWS, TSA, hash chain).
- [x] Implementar empaquetado `.evidence` (builder + verifier).
- [x] Implementar verificador CLI independiente.
- [ ] Finalizar migraciones SQL versionadas (2/5 aprobadas).
- [ ] Implementar procesador de pagos (worker, fulfillment, recovery).
- [ ] Implementar API HTTP pública.
- [ ] Añadir pruebas de corrupción, duplicados y confusión de algoritmos.
- [ ] Integrar TSA y proveedor de firma con credenciales reales.
- [ ] Completar revisión legal, de privacidad y seguridad externa.

---

```text
┌─[ 11 ]────────────────────────────────────────────────────────── CONTRIBUIR ─┐
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

```text
> IMPORTANTE: Contribuciones externas no aceptadas en la fase actual.
> El proyecto no cuenta aún con canal de moderación formalizado ni equipo
> de revisión asignado. Consulta CONTRIBUTING.md para el proceso previsto.
```

Antes de contribuir (cuando se abra el canal):

1. Lee [`CONTRIBUTING.md`](CONTRIBUTING.md) y [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
2. No incluyas secretos, certificados privados ni evidencia real.
3. Usa únicamente datos sintéticos en ejemplos y pruebas.
4. Documenta decisiones que afecten formatos, algoritmos o compatibilidad.

---

```text
┌─[ 12 ]───────────────────────────────────────────────────────────── LICENCIA ─┐
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

```text
  Código          ──▶  MIT (LICENSE)
  Documentación   ──▶  CC-BY-4.0 (LICENSE-DOCS.md)
```

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
║   root@evidence:~# █                                                     ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
```
