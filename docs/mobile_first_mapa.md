# Version movil optimizada del mapa

Fecha: 2026-06-21

Alcance: mejoras mobile first en `index.html` para la exploracion del mapa sonoro.

## Que cambio

- En celular, el mapa pasa a ser el protagonista visual y ocupa casi toda la pantalla.
- El panel inferior ahora funciona como bottom sheet con tres estados:
  - `collapsed`: busqueda, Filtros, Lista y Aportar.
  - `mid`: lista de historias para explorar.
  - `expanded`: filtros tactiles.
- La lista deja de ocupar la entrada inicial y se abre desde el boton `Lista`.
- Al tocar un punto en movil, primero aparece una tarjeta compacta con:
  - titulo,
  - tipo/fuente/lugar,
  - boton `Escuchar`,
  - boton `Detalles`.
- `Detalles` abre la ficha sonora completa optimizada para pulgar.
- Los filtros moviles ahora incluyen:
  - tipo de contenido,
  - categorias actuales,
  - periodo,
  - ruta sonora y puntos clave.

## Como funciona la experiencia movil

1. La persona entra al mapa y ve principalmente el territorio con los puntos sonoros.
2. Puede buscar desde el panel inferior colapsado.
3. Puede abrir `Filtros` para acotar por tipo, categoria o periodo.
4. Puede tocar `Lista` para ver historias sin que la lista domine la primera pantalla.
5. Al tocar un punto, se muestra una tarjeta breve.
6. Desde esa tarjeta puede escuchar directamente o abrir `Detalles`.
7. `Aportar` lleva a `captura.html`.

## Que no se toco

- No se modifico Supabase.
- No se modifico `captura.html`.
- No se modifico `curaduria.html`.
- No se modifico el arreglo `SOUND_POINTS`.
- No se cambio la experiencia de escritorio.
- No se elimino el onboarding, la analitica, el contador dinamico ni la carga de testimonios aprobados.

## Pruebas realizadas

- Validacion JavaScript de los scripts embebidos de `index.html`.
- Revision estatica de que no hay cambios en datos de `SOUND_POINTS`.
- Revision de reglas moviles para:
  - 360 x 740,
  - 390 x 844,
  - 412 x 915,
  - escritorio mayor a 1024 px.
- Verificacion de que los cambios estan encapsulados en reglas moviles y logica condicional `max-width: 768px`.

## Criterios de operacion

- En escritorio debe seguir apareciendo el panel lateral tradicional.
- En movil debe iniciar el mapa como pantalla principal.
- `Filtros`, `Lista` y `Aportar` deben estar disponibles desde el bottom sheet.
- Tocar un punto debe abrir primero la tarjeta compacta.
- `Detalles` debe abrir la ficha completa con reproductor o enlace de escucha.
