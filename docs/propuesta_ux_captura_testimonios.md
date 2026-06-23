# Propuesta UX/UI para captura de testimonios

Fecha: 2026-06-23

Alcance: rediseño visual y de interacción de `captura.html`. No modifica backend, Supabase, RLS, `index.html` ni `curaduria.html`.

## Objetivo de UX

Reducir la fricción para que una persona pueda entender la página en menos de 3 segundos:

```text
1. Grabar audio.
2. Subir audio.
3. Enviar para revisión.
```

La pantalla se diseñó como una experiencia de nota de voz, no como formulario académico.

## Estructura propuesta

### Primera pantalla

- Título principal: `COMPARTE TU HISTORIA EN AUDIO`.
- Subtítulo: `Tu voz forma parte de la memoria de Acapulco.`
- Caja cálida: `SOLO 30 SEGUNDOS A 1 MINUTO`.
- Botón principal: `GRABAR MI HISTORIA`.
- Botón secundario: `SUBIR AUDIO DE MI TELÉFONO`.
- Tres indicadores de confianza:
  - No pedimos tu nombre.
  - No pedimos tu teléfono.
  - Tu audio será revisado antes de publicarse.

### Flujo progresivo

Paso 1: Audio.

La persona graba desde el navegador si el teléfono lo permite, o sube un archivo. La grabación se convierte en archivo y usa el mismo flujo existente de Supabase.

Paso 2: Tema.

Se muestran botones grandes para clasificar el relato:

```text
Mi experiencia
Mi familia
Mi colonia
Mi trabajo o escuela
```

Y botones visuales para perfil:

```text
Habitante
Docente
Salud
Rescatista
Estudiante
Otro
```

Paso 3: Enviar.

Se muestran consentimientos cortos y el botón final.

## Elementos eliminados de la vista principal

- Introducción larga.
- Texto institucional extenso.
- Explicaciones metodológicas dentro del formulario.
- Vista previa técnica.
- Campos visibles de nombre, comunidad, municipio, localidad, fecha e entrevistador.
- Ubicación exacta y mapa como paso visible.
- Listas largas de perfiles.
- Mensajes técnicos de Supabase para usuarios finales.

Los datos necesarios siguen presentes como campos ocultos o valores por defecto para conservar compatibilidad.

## Elementos simplificados

- `alias` queda por defecto como `Anónimo`.
- `description` queda como descripción breve genérica, porque el contenido real está en el audio.
- `community`, `municipality`, `locality`, `interviewer` e `interview_date` se autocompletan para no bloquear el envío.
- `tipo_relato` se elige con botones grandes.
- `perfil_participante` se elige con botones visuales.
- `testimony_type` mantiene el mapeo legacy compatible con el CHECK de Supabase.
- La ubicación pasa a segundo plano y no se solicita como paso principal.

## Compatibilidad técnica conservada

El payload mantiene:

```text
status = pending
capture_mode = public_web
audio_bucket = testimonios-audio
audio_path = pending/<uuid>/<archivo>
tipo_relato
perfil_participante
testimony_type legacy
consent_archive_pending_review
consent_understands_not_auto_published
```

No se cambió estructura de Supabase ni políticas RLS.

## Estimación de mejora de conversión

Sin analítica A/B todavía, la estimación razonable es:

```text
+20% a +40% en intentos de envío
+15% a +30% en envíos completados
```

Motivos:

- Se elimina la percepción de formulario largo.
- El CTA principal aparece de inmediato.
- La persona puede grabar directamente como nota de voz.
- Se reducen campos visibles obligatorios.
- Se eliminan decisiones técnicas antes del audio.

La medición real debe hacerse comparando:

```text
visitas a captura.html
clic en grabar/subir
audio seleccionado o grabado
submit_testimony
registros pending en submissions
```

## Riesgos pendientes

- `MediaRecorder` no está disponible en todos los navegadores; por eso se mantiene `Subir audio de mi teléfono`.
- Algunos navegadores generan audio `webm`; el frontend ahora lo acepta.
- La grabación local no sustituye validación comunitaria ni revisión humana.
- La tasa real de conversión debe medirse con eventos, no asumirse.
