# 🔒 Política de Seguridad

## Versiones soportadas

| Versión | Soportada |
|---------|-----------|
| 0.x (desarrollo) | ✅ |
| 1.x (futuro) | ✅ |

## Reporte de vulnerabilidades

**No abra issues públicos para vulnerabilidades de seguridad.**

### Canal oficial

Use **GitHub Security Advisories** del repositorio:

1. Ve a la pestaña **Security** del repositorio.
2. Clic en **Report a vulnerability**.
3. Completa el formulario privado.

Este canal es privado, no expone datos personales y queda registrado en el propio repositorio.

### Formato del reporte
Versión afectada:

Componente:

Descripción:

Pasos para reproducir:

Impacto estimado:

Mitigación sugerida (opcional):

### Qué NO hacer

- ❌ No abrir un issue público.
- ❌ No enviar detalles por redes sociales.
- ❌ No publicar pruebas de concepto sin coordinación previa.

## Tiempos de respuesta

| Severidad | Acuse de recibo | Fix estimado |
|-----------|-----------------|--------------|
| Crítica | 24 horas | 7 días |
| Alta | 48 horas | 14 días |
| Media | 5 días | 30 días |
| Baja | 10 días | 90 días |

## Alcance

**En alcance**:
- Código fuente en `src/`
- Migraciones en `migrations/`
- Configuración en `.github/workflows/`
- Dockerfiles y compose

**Fuera de alcance**:
- Servicios de terceros (Mercado Pago, TSA, KMS)
- Infraestructura del despliegue final
- Dependencias externas (reportar upstream)

## Divulgación responsable

Seguimos **coordinated disclosure**:

1. Reporte privado vía GitHub Security Advisories.
2. Confirmación de recepción.
3. Fix en rama privada.
4. Release con parche.
5. Divulgación pública 30 días después del fix, con crédito al reportero si lo autoriza.
