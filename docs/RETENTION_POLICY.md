# 📅 Política de Retención

## Retención configurable

| Política | Duración | Aplica a |
|----------|----------|----------|
| `creator` | 1 año | Creadores individuales |
| `standard` | 5 años | Uso general |
| `commerce_mx` | 10 años | Referencia para comerciantes en actos de comercio |
| `custom` | Configurable | Casos específicos |

> [!CAUTION]
> La retención de 10 años se ofrece como opción **alineada con** NOM-151-SCFI-2016, no como obligación universal. NOM-151 aplica bajo supuestos específicos de actos de comercio. Cada usuario debe determinar su obligación específica con asesoría legal.

## Qué se retiene

| Elemento | Retención |
|----------|-----------|
| `content_hash` | Permanente |
| `private_commitment` | Según política |
| `token.rfc3161` | Permanente |
| `manifest.payload.json` | Permanente |
| `evidence-report.pdf` | Según política |
| Archivo original | **No aplica en MVP** (no se almacena) |
| Datos personales del titular | Según política |
| Logs de auditoría | Mínimo 10 años |
| Enlaces públicos | Revocables en cualquier momento |

## Eliminación

La eliminación se ejecuta:

1. Por solicitud del titular (derechos ARCO).
2. Por expiración de la política de retención.
3. Por acción administrativa en caso de uso indebido.

La eliminación **no** borra hashes ni tokens de tiempo, porque:

- No contienen datos personales por sí mismos.
- Son necesarios para la verificación criptográfica.
- Su eliminación rompería la cadena de auditoría.

## Exportación

El titular puede exportar en cualquier momento:

- El paquete `.evidence` completo.
- El `evidence-report.pdf`.
- Los metadatos asociados.
- El log de eventos de su evidencia.

## Contacto

Para solicitudes de retención, eliminación o exportación, use el canal indicado en [`SECURITY.md`](../SECURITY.md).
