# Politica de Seguridad

## Versiones soportadas

| Version | Soportada |
|---------|-----------|
| 0.x (desarrollo) | Si |
| 1.x (futuro) | Si |

## Reporte de vulnerabilidades

No abra issues publicos para vulnerabilidades de seguridad.

### Canal oficial

Use GitHub Security Advisories del repositorio:

1. Ve a la pestana Security del repositorio.
2. Clic en Report a vulnerability.
3. Completa el formulario privado.

### Formato del reporte

- Version afectada:
- Componente:
- Descripcion:
- Pasos para reproducir:
- Impacto estimado:
- Mitigacion sugerida (opcional):

### Que NO hacer

- No abrir un issue publico.
- No enviar detalles por redes sociales.
- No publicar pruebas de concepto sin coordinacion previa.

## Proceso de respuesta

El proyecto se encuentra en fase de diseno, sin capacidad operativa de respuesta a incidentes establecida. Los reportes seran atendidos en la medida de lo posible, segun disponibilidad y severidad.

No se ofrecen plazos fijos de correccion mientras no exista un equipo con dedicacion formal a la operacion y soporte del sistema.

Cuando el proyecto entre en operacion, esta seccion se actualizara con niveles de servicio, responsables y canales formalizados.

## Alcance

En alcance:
- Codigo fuente en src/
- Migraciones en migrations/
- Configuracion en .github/workflows/
- Dockerfiles y compose

Fuera de alcance:
- Servicios de terceros (Mercado Pago, TSA, KMS)
- Infraestructura del despliegue final
- Dependencias externas (reportar upstream)

## Divulgacion responsable

Se sigue coordinated disclosure:

1. Reporte privado via GitHub Security Advisories.
2. Confirmacion de recepcion.
3. Fix en rama privada.
4. Release con parche.
5. Divulgacion publica tras el fix, con credito al reportero si lo autoriza.

## Solicitudes de privacidad y retencion

Este documento no es el canal para ejercer derechos ARCO, solicitar eliminacion de datos o consultar politicas de retencion.

Esas solicitudes deben dirigirse por un canal de privacidad especifico, que sera publicado antes del inicio de operaciones comerciales. Ver docs/DATA_PROTECTION.md.
