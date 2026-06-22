# Auditoria UX movil de Punto Cero

Fecha: 2026-06-21

Alcance: auditoria y propuesta de experiencia movil para `index.html`.

No se modifico `index.html`, Supabase, `captura.html` ni `curaduria.html`.

## 1. Diagnostico ejecutivo

Punto Cero funciona bien en escritorio porque la logica principal es de pantalla amplia: mapa + panel lateral + filtros + lista. En celular, el sitio ya tiene una adaptacion parcial: el mapa ocupa la parte superior, el sidebar se vuelve una franja inferior, existe una navegacion movil y la ficha sonora usa `audio-sheet`.

El problema es que la experiencia movil todavia se siente como una version comprimida del escritorio. Para una persona que entra desde celular, la interfaz compite en tres frentes:

- mirar el mapa,
- entender la lista de historias,
- encontrar como escuchar o aportar.

La prioridad movil deberia ser mas clara:

1. descubrir puntos,
2. escuchar historias,
3. compartir testimonio.

## 2. Estado movil actual observado en `index.html`

El breakpoint principal esta en `@media (max-width: 768px)`.

Comportamiento actual:

- `body` cambia a columna.
- `#map` se muestra arriba con `42vh`.
- `#sidebar` ocupa abajo `58vh`.
- Se ocultan elementos pesados: header lateral, filtros de escritorio, busqueda de escritorio, timeline, estadisticas y footer.
- Aparece `#mobile-nav` con selector de categoria y busqueda.
- `#point-list` queda como lista scrollable.
- `#audio-sheet` aparece como panel inferior al seleccionar un punto.
- `#mobile-bottom-nav` ofrece `Historias`, `Mapa`, `Aportar`.
- `#fab-add` se transforma visualmente en `Aportar`.
- `#legend`, `#stats` y controles MapLibre se ocultan o reducen.

Esto es una buena base, pero aun no es una experiencia mobile first completa.

## 3. Problemas detectados

### 3.1 Espacio vertical

El reparto fijo `42vh / 58vh` hace que el mapa y la lista compitan siempre. En telefonos pequenos, ninguno de los dos respira:

- el mapa puede quedar demasiado bajo para explorar territorialmente;
- la lista puede sentirse como un panel permanente, no como una herramienta secundaria;
- al abrir `audio-sheet`, se suma otro panel sobre el panel inferior.

Riesgo: la pantalla se convierte en capas verticales acumuladas.

### 3.2 Panel lateral convertido en bloque inferior, pero no en bottom sheet

El `#sidebar` ya esta abajo, pero sigue siendo conceptualmente un panel fijo. No tiene estados claros:

- colapsado,
- medio abierto,
- expandido.

En una interfaz tipo Google Maps, el panel inferior debe poder cambiar de altura segun la accion del usuario. Ahora no hay una jerarquia movil clara entre mapa, lista y ficha.

### 3.3 Filtros dificiles de descubrir

En movil se reduce la categoria a `#mob-cat-sel` y la busqueda a `#mob-search-inp`. Esto ahorra espacio, pero es limitado:

- el select nativo no explica categorias;
- no incluye periodo, puntos clave ni ruta sonora en una estructura tactil equivalente;
- se pierde la lectura cultural de las categorias.

Riesgo: el usuario cree que solo puede buscar o elegir una categoria, pero no entiende el corpus.

### 3.4 Lista demasiado protagonista al entrar

La lista ocupa gran parte de la pantalla despues de entrar al mapa. Aunque favorece escuchar historias, contradice el objetivo nuevo de "pantalla inicial: mapa completo".

Riesgo: el usuario siente que entro a una lista de episodios, no a un mapa sonoro.

### 3.5 Interaccion tactil con puntos

Ya existe manejo de `touchend` para puntos individuales y `audio-sheet` movil. Aun asi, la seleccion se podria sentir brusca:

- tocar un punto abre ficha completa;
- no hay estado intermedio de "preview" breve;
- no hay una tarjeta inferior compacta con titulo, tipo, fuente y CTA principal.

Riesgo: el usuario pierde contexto espacial al abrir una ficha grande.

### 3.6 Reproductor y pulgar

El `audio-sheet` tiene buen camino: boton primario, descripcion y reproductor. Pero puede mejorar:

- CTA principal debe quedar cerca del pulgar y visible sin scroll;
- cerrar, compartir y aportar no deben competir;
- para Spotify, conviene diferenciar "abrir Spotify" de reproducir audio interno;
- para audio nativo de testimonios aprobados, el control debe ser grande y persistente.

### 3.7 Scroll y capas

Hay varios elementos con scroll potencial:

- lista inferior,
- `audio-sheet`,
- modal onboarding,
- popup MapLibre en algunos casos.

Riesgo: en celular aparecen gestos ambiguos: arrastrar mapa vs. desplazar lista vs. desplazar ficha.

### 3.8 Lectura

Los titulos largos y metadatos compiten con descripcion, etiquetas y reproductor. La ficha movil deberia privilegiar:

- titulo,
- tipo de fuente,
- lugar,
- boton escuchar,
- descripcion breve,
- metadatos secundarios colapsables.

### 3.9 Aportar testimonio

El enlace `Aportar` existe, pero puede competir con acciones de escucha. Debe estar visible, pero no imponerse sobre el acto principal de escuchar.

## 4. Principios para version movil

1. Mapa primero, lista despues.
2. Escuchar antes que filtrar.
3. Un gesto, una consecuencia.
4. Panel inferior con estados claros.
5. Filtros como herramienta desplegable, no como barra permanente.
6. Botones grandes, cerca del pulgar.
7. Sin cambios de escritorio.
8. Sin tocar Supabase ni curaduria.

## 5. Propuesta Mobile First

### 5.1 Pantalla inicial

Al entrar al mapa en celular:

- mostrar mapa casi completo;
- mostrar una barra inferior colapsada con busqueda breve y accesos;
- mantener boton de ayuda discreto;
- mantener boton `Aportar` como accion secundaria.

Wireframe:

```text
┌──────────────────────────────┐
│            MAPA              │
│                              │
│     puntos sonoros visibles  │
│                              │
│                    ? ayuda   │
│                              │
│                              │
├──────────────────────────────┤
│  Buscar historias...     ⌕   │  ← bottom sheet colapsado
│  [Filtros] [Lista] [Aportar] │
└──────────────────────────────┘
```

Estado recomendado:

- `#map`: 100vh o `calc(100vh - bottom-sheet-collapsed)`.
- `#sidebar`: transformado en `#mobile-bottom-sheet`.
- lista oculta inicialmente, accesible desde boton `Lista`.

### 5.2 Bottom sheet con estados

Reemplazar la franja fija inferior por un bottom sheet con tres estados:

| Estado | Altura sugerida | Uso |
| --- | --- | --- |
| Colapsado | 92-112px | Buscar, filtros, lista, aportar. |
| Medio | 42-50vh | Mostrar lista breve de historias. |
| Expandido | 82-88vh | Explorar lista completa y filtros. |

Wireframe:

```text
COLAPSADO
┌──────────────────────────────┐
│  ─────                       │
│  Buscar voces, lugares...    │
│  Filtros   Lista   Aportar   │
└──────────────────────────────┘

MEDIO
┌──────────────────────────────┐
│  ─────                       │
│  Historias cercanas/visibles │
│  • Historia 1        Escuchar│
│  • Historia 2        Escuchar│
│  • Historia 3        Escuchar│
└──────────────────────────────┘

EXPANDIDO
┌──────────────────────────────┐
│  ─────                       │
│  Buscar                      │
│  Filtros aplicados           │
│  Lista completa              │
│  ...                         │
└──────────────────────────────┘
```

### 5.3 Seleccion de punto

Al tocar un punto del mapa:

1. No abrir inmediatamente una ficha larga.
2. Abrir una tarjeta inferior compacta.
3. Mostrar CTA de escucha claro.
4. Permitir expandir para detalles.

Wireframe:

```text
┌──────────────────────────────┐
│            MAPA              │
│         ● punto activo       │
│                              │
├──────────────────────────────┤
│  ─────                       │
│  Titulo de la pieza          │
│  Radio · Ciudad de Mexico    │
│                              │
│  [ Escuchar ]     [Detalles] │
└──────────────────────────────┘
```

Estado expandido:

```text
┌──────────────────────────────┐
│  ─────                       │
│  Titulo completo             │
│  Fuente / tipo / fecha       │
│  [ Escuchar en Spotify ]     │
│  Descripcion breve           │
│  Etiquetas                   │
│  Compartir punto             │
└──────────────────────────────┘
```

### 5.4 Filtros

Mover filtros a un panel desplegable desde boton `Filtros`.

Contenido sugerido:

- Tipo de contenido:
  - Testimonios ciudadanos
  - Radio
  - Podcast
  - Musica
- Categorias actuales:
  - Cultural
  - Urbano
  - Trabajo
  - Ritual
  - Natural
- Periodo:
  - Octubre 2023
  - Noviembre 2023
  - Diciembre 2023
  - 2024
  - 2025
- Accesos:
  - Puntos clave
  - Ruta sonora
  - Ver todos

Wireframe:

```text
┌──────────────────────────────┐
│ Filtros                  ×   │
│                              │
│ Tipo de contenido            │
│ [Testimonios] [Radio]        │
│ [Podcast]    [Musica]        │
│                              │
│ Categorias                   │
│ [Cultural] [Urbano]          │
│ [Trabajo]  [Ritual] [Natural]│
│                              │
│ Periodo                      │
│ [Oct 23] [Nov 23] [2024]     │
│                              │
│ [Aplicar filtros]            │
└──────────────────────────────┘
```

### 5.5 Listado

El listado debe ser accesible, pero no permanente al inicio.

Recomendacion:

- boton `Lista` abre bottom sheet en estado medio;
- mostrar primero puntos visibles en el mapa o cercanos al centro actual;
- cada item debe tener:
  - titulo maximo 2 lineas,
  - fuente/tipo,
  - boton `Escuchar`,
  - categoria como color secundario.

Wireframe:

```text
┌──────────────────────────────┐
│ Historias visibles       ×   │
│                              │
│ ● Titulo de historia         │
│   Podcast · Acapulco         │
│                  [Escuchar]  │
│                              │
│ ● Titulo de historia         │
│   Testimonio · Colonia...    │
│                  [Escuchar]  │
└──────────────────────────────┘
```

### 5.6 Reproductor

Optimizar para pulgar:

- CTA principal ancho y alto: minimo 48px.
- Si es Spotify: `Escuchar en Spotify`.
- Si es audio nativo: control HTML visible y grande.
- Mantener cerrar arriba/derecha, pero no como accion principal.
- Mantener descripcion bajo el CTA, no antes.

Orden recomendado:

1. Titulo.
2. Tipo/fuente/lugar.
3. Boton escuchar.
4. Reproductor o enlace.
5. Descripcion.
6. Metadatos.
7. Compartir.

## 6. Arquitectura visual propuesta

### Estado A: entrada al mapa

```text
┌──────────────────────────────┐
│ MAPA FULL                    │
│                              │
│ puntos + clusters            │
│                              │
│ ?                            │
├──────────────────────────────┤
│  ─────                       │
│  Buscar voces o lugares      │
│  Filtros | Lista | Aportar   │
└──────────────────────────────┘
```

### Estado B: punto seleccionado

```text
┌──────────────────────────────┐
│ MAPA                         │
│      ● seleccionado          │
├──────────────────────────────┤
│  ─────                       │
│  Titulo                      │
│  Radio · CDMX · 7 min        │
│  [Escuchar] [Detalles]       │
└──────────────────────────────┘
```

### Estado C: ficha expandida

```text
┌──────────────────────────────┐
│ MAPA reducido detras         │
├──────────────────────────────┤
│  ─────                    ×  │
│  Titulo completo             │
│  Fuente / categoria          │
│  [Escuchar en Spotify]       │
│  Descripcion                 │
│  Etiquetas                   │
│  Compartir punto             │
└──────────────────────────────┘
```

### Estado D: filtros

```text
┌──────────────────────────────┐
│ Filtros                   ×  │
│ Tipo contenido               │
│ Categorias                   │
│ Periodo                      │
│ Ruta sonora / puntos clave   │
│ [Aplicar] [Limpiar]          │
└──────────────────────────────┘
```

## 7. Priorizacion de acciones

### Prioridad 1: escuchar historias

- CTA `Escuchar` siempre visible en tarjeta de punto.
- Audio sheet compacto antes de ficha completa.
- Lista enfocada en piezas audibles, no en metadatos.

### Prioridad 2: descubrir puntos

- Mapa completo al iniciar.
- Puntos visibles sin obstrucciones.
- Lista como complemento, no como pantalla principal.

### Prioridad 3: compartir testimonios

- `Aportar` visible en barra inferior.
- No competir con `Escuchar`.
- Llevar siempre a `captura.html`, no al modal de punto historico.

## 8. Plan de implementacion por fases

### Fase 1: estructura movil sin tocar escritorio

- Crear clases/IDs moviles:
  - `#mobile-bottom-sheet`
  - `.sheet-collapsed`
  - `.sheet-mid`
  - `.sheet-expanded`
- Mantener escritorio intacto.
- Encapsular CSS dentro de `@media (max-width: 768px)`.

### Fase 2: tarjeta compacta de punto

- Modificar solo flujo movil de `flyToPoint(p)`.
- En movil, abrir tarjeta compacta primero.
- Boton `Detalles` expande al `audio-sheet` actual.

### Fase 3: filtros desplegables

- Reemplazar `#mob-cat-sel` por boton `Filtros`.
- Crear panel con chips tactiles.
- Mantener `activeCategory`, `activePeriod`, `activeImportance` existentes.

### Fase 4: lista secundaria

- Boton `Lista` abre bottom sheet medio.
- Renderizar `point-list` dentro del sheet.
- Ordenar por puntos visibles o por categoria activa.

### Fase 5: reproductor optimizado

- Ajustar `buildMobileSheetHTML(p)`:
  - CTA arriba,
  - descripcion despues,
  - metadatos colapsables.
- Para testimonios ciudadanos aprobados con audio nativo, priorizar control HTML.

### Fase 6: QA movil

Probar:

- 360 x 740
- 390 x 844
- 412 x 915
- iPhone SE
- Android Chrome
- Safari iOS

## 9. Riesgos y cuidados

- No romper escritorio: evitar cambios globales en `#sidebar`, `#map`, `flyToPoint` sin condicional movil.
- No tocar Supabase ni datos.
- No cambiar `SOUND_POINTS`.
- No cambiar `captura.html` salvo una fase futura explicitamente autorizada.
- Cuidar stacking context: `audio-sheet`, `mobile-bottom-nav`, onboarding y MapLibre usan z-index.
- Evitar doble scroll: solo un panel debe tener scroll activo por estado.

## 10. Criterios de exito

- Al entrar en celular, el mapa ocupa la experiencia principal.
- En menos de 5 segundos se entiende que se puede tocar un punto y escuchar.
- Un punto seleccionado abre una tarjeta clara, no una ficha abrumadora.
- Los filtros se entienden como herramienta opcional.
- La lista es accesible, pero no domina la pantalla inicial.
- El boton `Aportar` es visible, pero secundario frente a `Escuchar`.
- Escritorio queda visual y funcionalmente igual.

## 11. Recomendacion final

Implementar una version movil en capas:

1. mapa completo,
2. bottom sheet colapsado,
3. tarjeta compacta al seleccionar punto,
4. ficha expandida para escuchar,
5. filtros y lista como herramientas secundarias.

Esto conserva la identidad actual del proyecto y evita convertir Punto Cero en una app tecnica. La experiencia movil debe sentirse como una caminata sonora: mirar, tocar, escuchar y, si se desea, aportar.
