# Diseño del Sistema de Captura de Testimonios

Este sprint agrega una página independiente de captura sin tocar el mapa actual. La producción existente en `puntoceroacapulco.online` no debe romperse ni recibir publicaciones automáticas.

Punto Cero contempla dos formas de ingreso:

1. **Captura pública**: visitantes del mapa pueden grabar o subir un audio desde el sitio.
2. **Captura investigadora**: el equipo puede grabar testimonios en comunidades rurales, incluso sin internet, y cargarlos después.

Todo registro entra a una cola de pendientes. La publicación en el mapa ocurre solo después de revisión ética y curatorial.

## A. Flujo público

```text
Visitante abre captura.html
  -> escribe nombre o seudónimo
  -> escribe comunidad y municipio
  -> describe el testimonio
  -> sube archivo de audio
  -> captura GPS si lo desea y el navegador lo permite
  -> acepta consentimiento informado
  -> descarga un JSON pendiente
  -> equipo recibe/revisa el JSON y el audio
  -> curaduría decide si se integra al corpus público
```

Reglas:

- La página pública no guarda en servidor en el MVP estático.
- La página no modifica `sound_points.json`.
- La página no publica nada en el mapa.
- La persona debe saber que el testimonio queda pendiente de revisión.
- GPS es opcional y debe revisarse antes de publicación.

## B. Flujo investigador

```text
Investigador o entrevistador comunitario captura en campo
  -> graba audio en celular o sube archivo existente
  -> captura GPS interno si hay consentimiento
  -> captura comunidad y municipio manualmente
  -> registra consentimiento informado
  -> marca sensibilidad preliminar
  -> guarda registro offline
  -> sincroniza o descarga JSON cuando tenga internet
  -> equipo revisa
  -> administrador aprueba o restringe publicación
```

Reglas:

- Debe funcionar con conectividad limitada.
- Debe separar coordenada interna de coordenada pública.
- Debe permitir marcar testimonios sensibles desde campo.
- Debe evitar publicación automática.

## C. Campos mínimos

Campos mínimos para un registro pendiente:

- nombre o seudónimo;
- comunidad;
- municipio;
- descripción;
- archivo de audio;
- coordenadas, si se capturan;
- tipo de coordenada pública sugerida;
- sensibilidad preliminar;
- consentimiento informado;
- fecha de creación;
- estado `pending`;
- modo de captura.

## D. Campos para consentimiento

El consentimiento mínimo del prototipo registra:

- autorización para conservar el audio como pendiente;
- confirmación de que no se publicará automáticamente;
- permiso para solicitar más información;
- permiso opcional para considerar publicación después de revisión.

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

La arquitectura actual sigue siendo estática:

```text
public/index.html
public/captura.html
public/data/sound_points.json
public/data/submissions_pending.example.json
```

`captura.html` genera un JSON descargable. Ese archivo debe revisarse manualmente antes de cualquier integración.

Flujo MVP:

```text
captura.html
  -> JSON descargado
  -> carpeta local o nube privada
  -> revisión ética/curatorial
  -> eventual migración manual a un corpus enriquecido
  -> eventual publicación aprobada
```

## G. Arquitectura futura

La versión futura puede incorporar backend:

```text
Formulario público e investigador
  -> API de submissions
  -> almacenamiento privado de audio
  -> base de datos de metadatos
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
- manejo de consentimiento;
- transcripción;
- publicación controlada;
- retiro o despublicación.

## H. Primer prototipo recomendado

El primer prototipo recomendado es `public/captura.html`.

Debe permitir:

- nombre o seudónimo;
- comunidad;
- municipio;
- descripción;
- subir archivo de audio;
- capturar coordenadas si el navegador lo permite;
- seleccionar tipo de coordenada pública sugerida;
- marcar sensibilidad preliminar;
- aceptar consentimiento;
- descargar un JSON pendiente.

Este prototipo sirve para probar el flujo sin afectar el mapa actual ni la producción existente.
