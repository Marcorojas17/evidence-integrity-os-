# ⚖️ Marco legal de referencia — México

> [!CAUTION]
> Este documento describe **alineación de diseño**, no cumplimiento certificado ni admisibilidad automática. La cita exacta de artículos debe validarse con asesoría legal mexicana antes de usarse en procedimientos judiciales.

---

## 1. NOM-151-SCFI-2016

**Norma Oficial Mexicana**, publicada en el DOF el **30 de marzo de 2017**, que establece los requisitos para la conservación de mensajes de datos y digitalización de documentos.

### Relevancia para el sistema

- La constancia de conservación de mensajes de datos solo puede emitirla un **PSC (Prestador de Servicios de Certificación) acreditado** ante la Secretaría de Economía.
- Un sello RFC 3161 **no equivale** a una constancia NOM-151.
- La norma aplica bajo supuestos específicos de actos de comercio, no de forma universal.

### Cómo se alinea el diseño

- El sistema **no emite** constancias NOM-151.
- El sistema **puede integrar** constancias NOM-151 emitidas por un PSC autorizado, como producto separado.
- La retención de 10 años se ofrece como opción configurable, no como regla universal.

### Pendiente

- Validar con abogado los supuestos exactos de aplicación.
- Confirmar integración con un PSC específico antes de comercializar.

---

## 2. Código de Comercio — Art. 97

**Uso de firma electrónica en mensajes de datos.** El artículo establece el marco para el uso de firma electrónica en actos de comercio y su valor probatorio.

### Relevancia para el sistema

- La firma PAdES del `evidence-report.pdf` **no equivale automáticamente** a una Firma Electrónica Avanzada (FEA) bajo el régimen mexicano.
- La FEA, bajo el Código de Comercio, requiere certificado emitido por un PSC mexicano acreditado.
- El sistema puede integrar FEA si se contrata a un PSC.

### Cómo se alinea el diseño

- El MVP usa PAdES-B-T con certificado de CA reconocida internacionalmente.
- Se documenta la diferencia entre PAdES y FEA.
- La integración con PSC mexicano se ofrece como evolución.

### Pendiente

- Revisión legal sobre el uso de PAdES en procedimientos mexicanos.
- Definir si se contrata PSC para emitir FEA.

---

## 3. Código Nacional de Procedimientos Penales — Art. 265

**Valoración de datos y pruebas.** El órgano jurisdiccional asigna libremente el valor correspondiente a cada dato o prueba.

### Relevancia para el sistema

- El artículo regula la valoración **general** de datos y pruebas, no específicamente "prueba digital".
- El juez decide la admisibilidad y el peso de la evidencia.
- Un paquete `.evidence` bien construido **facilita** la pericia, pero **no garantiza** admisibilidad.
- La cadena de custodia es un factor determinante.

### Cómo se alinea el diseño

- El paquete `.evidence` conserva cadena de custodia verificable.
- El verificador independiente permite reproducir la verificación por un perito.
- La documentación técnica facilita el peritaje.

### Pendiente

- Revisión con abogado penalista sobre requisitos específicos.
- Considerar jurisprudencia aplicable.

---

## 4. LFPDPPP

**Ley Federal de Protección de Datos Personales en Posesión de los Particulares**. Regula el tratamiento de datos personales por parte de privados.

### Relevancia para el sistema

- Los archivos registrados pueden contener datos personales.
- El titular de los datos debe otorgar consentimiento.
- El aviso de privacidad es obligatorio.
- Los derechos ARCO (Acceso, Rectificación, Cancelación, Oposición) deben poder ejercerse.

### Cómo se alinea el diseño

- Minimización de datos: solo se conservan hashes y metadatos mínimos.
- Separación entre datos identificables y hashes.
- Consentimiento explícito antes de exponer enlace público.
- Eliminación de datos identificables sin romper la verificación criptográfica.
- Aviso de privacidad documentado en `docs/DATA_PROTECTION.md`.

### Pendiente

- Revisión con abogado especialista en protección de datos.
- Registro del aviso de privacidad ante la autoridad competente, si aplica.

---

## 5. Referencias internacionales

- **RFC 3161** — sellado de tiempo (TSP).
- **RFC 8785** — JCS.
- **RFC 7797** — JWS Unencoded Payload.
- **ETSI EN 319 142-1** — perfiles PAdES.
- **ISO/IEC 27001** — gestión de seguridad (referencia de diseño).
- **ISO/IEC 27037** — guía forense digital (referencia técnica).

> Ninguna de estas referencias implica certificación.

---

## 6. Estado de este documento

| Aspecto | Estado |
|---------|--------|
| Redacción técnica | ✅ |
| Alineación de diseño | ✅ |
| Revisión legal profesional | ⚠️ Pendiente |
| Validación de citas exactas | ⚠️ Pendiente |

**Este documento no debe usarse como asesoría legal.** Antes de comercializar el sistema o usarlo en procedimientos judiciales, debe ser revisado por un abogado mexicano especializado en derecho digital, propiedad intelectual y protección de datos.
