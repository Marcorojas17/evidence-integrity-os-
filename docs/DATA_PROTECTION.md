# 🔐 Protección de Datos

## Principios aplicados

| Principio | Implementación |
|-----------|----------------|
| Minimización | Solo se conservan hashes y metadatos mínimos. |
| Finalidad | Los datos se usan exclusivamente para verificación de integridad. |
| Consentimiento | El titular autoriza explícitamente la verificación pública. |
| Acceso | Roles y permisos diferenciados. |
| Rectificación | El titular puede actualizar metadatos no criptográficos. |
| Cancelación | Eliminación de datos identificables sin romper la verificación. |
| Oposición | El titular puede desactivar el enlace público. |
| Seguridad | Cifrado en tránsito. Cifrado en reposo para datos sensibles. |

## Decisión MVP: sin archivo original

> [!IMPORTANT]
> **El MVP no almacena el archivo original del usuario.**
>
> Motivos:
> - Reduce superficie de exposición de datos personales.
> - Elimina la necesidad de definir formato de cifrado, versión de clave y control de acceso específico.
> - La verificación de estructura, firmas y sellos **no requiere el original**.
> - El titular conserva el original en su propio medio.
>
> Si en el futuro se activa el almacenamiento del original, deberá documentarse:
> - Formato contenedor y algoritmo de cifrado.
> - Versión de clave y política de rotación (KMS).
> - Control de acceso por rol.
> - Retención y procedimiento de eliminación.
> - Consentimiento explícito diferenciado.

## Separación de datos

| Tipo | Almacenamiento | Cifrado | Retención |
|------|----------------|---------|-----------|
| `content_hash` | Base de datos | No (es un hash público) | Permanente |
| `private_commitment` | Base de datos cifrada | Sí | Configurable |
| Datos personales del titular | Tabla separada | Sí | Configurable |
| Archivo original | **No se almacena en el MVP** | N/A | N/A |
| Logs de auditoría | Almacenamiento inmutable | Sí | 10 años |

## Derechos del titular (ARCO)

El titular puede ejercer:

1. **Acceso**: consultar sus datos.
2. **Rectificación**: corregir metadatos no criptográficos.
3. **Cancelación**: eliminar datos identificables.
4. **Oposición**: desactivar verificación pública.

Los hashes y tokens de tiempo **no se eliminan** porque:

- No contienen datos personales por sí mismos.
- Son necesarios para la verificación criptográfica.

## Sobre el `content_hash` y ataques de diccionario

El `content_hash` es un SHA-256 del archivo. Es público e interoperable por diseño.

> [!WARNING]
> Si el archivo tiene **baja entropía** (documento estándar, texto corto, imagen predecible), un tercero podría reproducir el hash por diccionario y deducir que el archivo corresponde a un contenido conocido. El `private_commitment` (HMAC) **no protege** al `content_hash` público contra este ataque. Solo aporta control adicional interno.

**Mitigación disponible para el titular**: usar el modo "privado" (sin página pública) y no publicar el `content_hash`.

## Aviso de privacidad

El aviso de privacidad completo debe publicarse antes de la operación comercial. Este documento describe las bases técnicas; el aviso legal debe ser revisado por abogado especialista en LFPDPPP.
