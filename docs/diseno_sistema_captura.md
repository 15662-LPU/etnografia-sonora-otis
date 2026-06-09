# Diseño del Sistema de Captura de Testimonios

Este documento describe la página independiente `captura.html`. Su función es recibir testimonios sonoros para revisión ética y curatorial sin tocar el mapa actual ni publicar nada automáticamente.

Punto Cero contempla dos formas de ingreso:

1. **Captura pública**: visitantes del mapa pueden subir un audio desde el sitio.
2. **Captura investigadora**: el equipo puede registrar testimonios en comunidades rurales, incluso con conectividad limitada, y cargarlos después.

Todo registro entra a una cola de pendientes. La publicación en el mapa ocurre solo después de revisión ética y curatorial.

La implementación actual conecta `captura.html` con Supabase para recibir audios en el bucket privado `testimonios-audio` y metadatos en la tabla `submissions`. La opción de descargar JSON se conserva como respaldo cuando no hay internet o falla el envío.

## A. Flujo público

```text
Visitante abre captura.html
  -> escribe nombre o seudónimo
  -> escribe comunidad, municipio y localidad
  -> describe el testimonio
  -> sube archivo de audio
  -> captura GPS si lo desea y el navegador lo permite
  -> acepta consentimiento informado
  -> envía audio y metadatos a Supabase
  -> recibe mensaje de testimonio enviado para revisión
  -> si falla la conexión, descarga un JSON pendiente
  -> equipo revisa el registro y el audio privados
  -> curaduría decide si se integra al corpus público
```

Reglas:

- La página pública guarda en una cola privada de Supabase, no en el mapa.
- La página no modifica `sound_points.json` ni `etnografia-sonora.geojson`.
- La página no publica nada automáticamente.
- La persona debe saber que el testimonio queda pendiente de revisión.
- GPS es opcional y debe revisarse antes de cualquier publicación.
- El respaldo JSON se usa para modo offline, error de red o carga manual posterior.

## B. Flujo investigador

```text
Investigador o entrevistador comunitario captura en campo
  -> graba audio en celular o sube archivo existente
  -> captura GPS interno si hay consentimiento
  -> captura comunidad y municipio manualmente
  -> registra consentimiento informado
  -> marca sensibilidad preliminar
  -> intenta enviar cuando haya internet
  -> si no hay conexión, descarga JSON
  -> equipo revisa
  -> administrador aprueba, restringe o rechaza publicación
```

Reglas:

- Debe funcionar con conectividad limitada.
- Debe separar coordenada interna de coordenada pública.
- Debe permitir marcar testimonios sensibles desde campo.
- Debe evitar publicación automática.
- Debe conservar trazabilidad entre audio, metadatos y consentimiento.

## C. Campos mínimos

Campos mínimos para un registro pendiente:

- nombre o seudónimo;
- comunidad;
- municipio;
- localidad;
- descripción;
- archivo de audio;
- fecha de entrevista;
- nombre del entrevistador;
- tipo de testimonio;
- coordenadas, si se capturan;
- tipo de coordenada pública sugerida;
- sensibilidad preliminar;
- consentimiento informado;
- estado `pending`;
- modo de captura.

## D. Campos para consentimiento

El consentimiento mínimo del formulario registra:

- autorización para conservar el audio como pendiente;
- confirmación de que no se publicará automáticamente;
- permiso para solicitar más información;
- permiso opcional para considerar publicación después de revisión;
- fecha y hora del registro del consentimiento;
- método de consentimiento: casillas del formulario web.

En una versión futura, el consentimiento debe separarse en:

- conservar en archivo interno;
- publicar audio completo;
- publicar fragmento;
- publicar transcripción;
- publicar nombre;
- publicar comunidad;
- publicar ubicación exacta;
- publicar ubicación aproximada;
- uso académico;
- retiro posterior del testimonio.

## E. Estados del registro

Estados recomendados:

- `draft`: registro incompleto.
- `offline_draft`: registro capturado sin internet.
- `pending`: enviado o descargado para revisión.
- `needs_info`: requiere completar datos.
- `reviewed`: revisado ética y curatorialmente.
- `sensitive`: requiere protección especial.
- `approved`: aprobado para publicarse.
- `published`: visible en mapa público.
- `private`: conservado internamente.
- `rejected`: no se integra al corpus.
- `withdrawn`: retirado por solicitud.

Regla:

```text
Solo approved o published puede alimentar el mapa público.
```

## F. Arquitectura MVP

La arquitectura actual sigue siendo estática en el sitio público, con Supabase como servicio de recepción privada:

```text
index.html
captura.html
data/submissions_pending.example.json
Supabase Storage: bucket privado testimonios-audio
Supabase Database: tabla submissions
```

`captura.html` intenta subir primero el audio al bucket privado `testimonios-audio` y después inserta los metadatos en `submissions` con `status = pending`. Si el envío falla, mantiene la opción de descargar el registro JSON para subirlo después.

Flujo MVP:

```text
captura.html
  -> audio privado en testimonios-audio
  -> metadatos en submissions con status pending
  -> fallback: JSON descargado
  -> revisión ética/curatorial
  -> eventual migración manual a un corpus enriquecido
  -> eventual publicación aprobada
```

Permisos del MVP:

- `anon` puede insertar registros pendientes y subir audios al bucket privado según las políticas RLS configuradas.
- `anon` no debe poder listar ni leer testimonios, audios ni datos sensibles.
- El administrador revisa desde Supabase con una cuenta autenticada.
- El mapa público no consume `submissions`.

## G. Arquitectura futura

La versión futura puede incorporar un panel de administración:

```text
Formulario público e investigador
  -> Supabase Storage privado
  -> tabla submissions
  -> cola de revisión
  -> panel de curaduría
  -> exportación pública JSON/GeoJSON
  -> mapa público
```

Componentes futuros:

- autenticación por rol;
- carga segura de audios;
- modo offline con sincronización;
- panel de revisión;
- historial de cambios;
- manejo granular de consentimiento;
- transcripción;
- publicación controlada;
- retiro o despublicación.

## H. Seguridad y revisión

Reglas operativas:

- Todo registro enviado desde `captura.html` entra con `status = pending`.
- Ningún registro pendiente se agrega automáticamente a `etnografia-sonora.geojson` ni al mapa.
- Las coordenadas exactas deben tratarse como internas hasta que la revisión decida si se publican exactas, aproximadas, simbólicas o desplazadas.
- Los audios permanecen en un bucket privado.
- No se usa `service_role` en el frontend.
- La publicación requiere aprobación ética y curatorial.

## I. Primer prototipo recomendado

El prototipo activo es `captura.html`.

Debe permitir:

- nombre o seudónimo;
- comunidad;
- municipio;
- localidad;
- descripción;
- subir archivo de audio;
- capturar coordenadas si el navegador lo permite;
- seleccionar tipo de coordenada pública sugerida;
- marcar sensibilidad preliminar;
- aceptar consentimiento;
- enviar a Supabase para revisión;
- descargar un JSON pendiente como respaldo.

Este prototipo sirve para probar el flujo sin afectar el mapa actual ni la producción existente.
