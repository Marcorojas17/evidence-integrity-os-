# 📘 Uso Manual — Guía sin terminal

Guía paso a paso para operar Evidence Integrity OS sin usar terminal ni automatización local.

> [!WARNING]
> Esta guía describe el flujo previsto. La interfaz web estará disponible tras completar el desarrollo del MVP. Hasta entonces, los pasos son una referencia de diseño.

---

## A. Preparar la evidencia

1. **Conserva el original** en un medio seguro, con acceso restringido.
2. **No renombres, edites ni reexportes** el archivo después de iniciar el proceso.
3. **Documenta el contexto**:
   - Fecha y hora de obtención.
   - Origen del archivo.
   - Persona responsable.
   - Circunstancias relevantes.
4. **Crea una copia de trabajo** para cargar en la plataforma. El original queda intacto.

## B. Registrar la evidencia

En la interfaz de la plataforma:

1. Selecciona **Nueva evidencia**.
2. Carga la copia de trabajo.
3. Revisa el nombre, tamaño y tipo de archivo detectados.
4. Lee y acepta:
   - El aviso de privacidad.
   - El consentimiento de verificación pública (si aplica).
   - La política de retención.
5. Confirma la creación del paquete `.evidence`.

El sistema calculará:

- `content_hash` (SHA-256) del archivo.
- `private_commitment` (HMAC) para uso privado.
- Token RFC 3161 emitido por la TSA externa.
- `evidence-report.pdf` con firma PAdES-B-T.

## C. Conservar el paquete

Guarda juntos, sin alterar:

- El archivo original.
- El paquete `.evidence`.
- El `evidence-report.pdf`.
- El identificador de verificación.
- La documentación del contexto de obtención.

**Mantén al menos dos respaldos** en ubicaciones separadas. Uno de ellos debe permanecer sin conexión cuando sea posible.

## D. Verificar manualmente

1. Abre el verificador público.
2. Introduce el identificador o carga el paquete `.evidence`.
3. Confirma que el `content_hash` del archivo local coincide con el registrado.
4. Revisa:
   - El sello de tiempo RFC 3161.
   - La cadena de firma PAdES.
   - El estado de revocación indicado.
5. Descarga o registra el resultado de la verificación para tu expediente.

> **Nunca compartas públicamente un archivo sensible solo para verificarlo.** Utiliza identificadores mínimos y aplica consentimiento explícito.

### Sobre el `content_hash` y el HMAC

- **`content_hash` (SHA-256)**: verificable por cualquier tercero que tenga el archivo. Si el archivo tiene baja entropía (por ejemplo, un documento estándar), un tercero podría comprobarlo por diccionario.
- **`private_commitment` (HMAC)**: prueba privada controlada por el sistema/titular. No protege al `content_hash` público contra ataques de diccionario. Sirve como control adicional interno.

## E. Qué hacer si algo no coincide

Si el `content_hash` no coincide:

1. **No modifiques el archivo** ni el paquete.
2. Documenta la discrepancia con capturas y fechas.
3. Contacta al soporte con:
   - Identificador de la evidencia.
   - Descripción del problema.
   - Resultado de la verificación.
4. No intentes "arreglar" el paquete por tu cuenta.

## F. Qué requiere el archivo original

| Acción | ¿Requiere el original? |
|--------|------------------------|
| Verificar estructura, firmas y sellos del paquete | ❌ No |
| Comparar un archivo específico contra el paquete | ✅ Sí (recalcular su `content_hash`) |
| Consultar el estado de un enlace público | ❌ No |
| Validar la cadena de confianza PAdES | ❌ No |

El MVP **no incluye el original dentro del paquete** por defecto.

## G. Eliminación y retención

Puedes solicitar la eliminación de:

- Datos personales asociados a la evidencia.
- El archivo original (si lo incluiste opcionalmente en el futuro).
- El enlace público de verificación.

La eliminación **no borra** los hashes ni los tokens de tiempo, porque son necesarios para la verificación criptográfica. Se elimina la vinculación con datos identificables.

Ver [`docs/RETENTION_POLICY.md`](../RETENTION_POLICY.md) y [`docs/DATA_PROTECTION.md`](../DATA_PROTECTION.md).

## H. Contacto

Para dudas sobre uso, verificación o eliminación, consulta el canal indicado en [`SECURITY.md`](../../SECURITY.md).
