# 🔐 Registro de Algoritmos

Postura criptográfica explícita del proyecto. Este documento declara qué algoritmos se aceptan, cuáles se deprecan, cuáles se prohíben, y cómo se gestiona su ciclo de vida.

**Filosofía**: lista cerrada, rechazo explícito, sin "compatibilidad por defecto". Un algoritmo que no está en la lista de aceptados se rechaza sin advertencia.

---

## 1. Algoritmos aceptados (v1)

### Hashes

| Algoritmo | Uso | Estado |
|-----------|-----|--------|
| SHA-256 | `content_hash` | ✅ Aceptado |
| BLAKE3 | Verificación rápida local (opcional) | ✅ Aceptado |
| HMAC-SHA256 | `private_commitment` | ✅ Aceptado |

### Firmas

| Algoritmo | Uso | Estado |
|-----------|-----|--------|
| ECDSA P-256 (ES256) | `manifest.jws.json` | ✅ Aceptado |
| RSA-PSS 2048+ (PS256) | Alternativa si se requiere compatibilidad | ✅ Aceptado |
| ECDSA P-384 (ES384) | Alternativa para mayor seguridad | ✅ Aceptado |

### Sellos de tiempo

| Estándar | Uso | Estado |
|----------|-----|--------|
| RFC 3161 | `token.rfc3161` | ✅ Aceptado |
| SHA-256 como `messageImprint` | Vinculación con el hash | ✅ Aceptado |

### Firmas PDF

| Perfil | Uso | Estado |
|--------|-----|--------|
| PAdES-B-T (ETSI EN 319 142-1) | `evidence-report.pdf` | ✅ Aceptado |
| PAdES-B-LT | Retención >2 años (futuro) | 🟡 Planificado |
| PAdES-B-LTA | Archivo a largo plazo (futuro) | 🟡 Planificado |

### Canonicalización

| Estándar | Uso | Estado |
|----------|-----|--------|
| RFC 8785 (JCS) | `manifest.payload.json` | ✅ Aceptado |

### Serialización JWS

| Opción | Uso | Estado |
|--------|-----|--------|
| RFC 7797 (b64=false, crit=["b64"]) | `manifest.jws.json` | ✅ Aceptado |
| RFC 7515 (JWS JSON Serialization) | Referencia teórica | ✅ Aceptado |

---

## 2. Algoritmos prohibidos

| Algoritmo | Motivo |
|-----------|--------|
| MD5 | Colisiones demostradas |
| SHA-1 | Colisiones demostradas |
| RSA PKCS#1 v1.5 (firmas) | Vulnerabilidades de padding |
| DES / 3DES | Clave insuficiente |
| RC4 | Sesgos estadísticos |
| `alg=none` (JWS) | Sin firma |
| HS256 con clave pública (JWS) | Confusión de algoritmo |
| EC P-192 | Curva débil |

Estos algoritmos deben **rechazarse explícitamente**, no aceptarse con advertencia.

---

## 3. Reglas de validación estrictas

### JWS (`manifest.jws.json`)

El verificador **debe**:

1. Rechazar si `alg` no está en la lista de aceptados.
2. Rechazar si `alg=none` está presente.
3. Rechazar si `crit` está vacío o ausente.
4. Rechazar si `b64` no aparece en `crit`.
5. Rechazar si `b64 != false` (el MVP usa payload detached).
6. Rechazar si `kid` no está en el header protegido.
7. Rechazar si `x5c` está ausente.
8. Verificar la firma solo después de las validaciones anteriores.

### Token RFC 3161

El verificador **debe**:

1. Parsear el ASN.1.
2. Verificar que `messageImprint.hashAlgorithm` sea SHA-256.
3. Verificar que `messageImprint.hashedMessage` coincida con `SHA256(JCS(manifest.payload.json))`.
4. Verificar la firma de la TSA sobre el token.
5. Verificar la cadena de certificados de la TSA contra una raíz confiable.
6. Verificar el estado de revocación de la TSA (OCSP/CRL).
7. **No** comparar `genTime` con `signed_at`. El único vínculo obligatorio es `messageImprint`.

### Firma PAdES (`evidence-report.pdf`)

El verificador **debe**:

1. Confirmar que el PDF no ha sido modificado tras la firma.
2. Verificar la firma PAdES según ETSI EN 319 142-1.
3. Verificar la cadena de confianza del certificado de firma.
4. Verificar el sello de tiempo embebido.
5. Consultar OCSP/CRL si el perfil es B-LT o B-LTA.

---

## 4. Ciclo de vida de algoritmos

| Estado | Significado | Acción del verificador |
|--------|-------------|------------------------|
| ✅ Aceptado | Se puede usar para nuevas firmas y se acepta en verificación | Procesar |
| 🟡 Planificado | En diseño, aún no implementado | Rechazar |
| ⚠️ Deprecado | Ya no se usa para nuevas firmas, pero se acepta en verificación histórica | Procesar con advertencia |
| ❌ Prohibido | No se acepta en ningún caso | Rechazar explícitamente |

### Transiciones
