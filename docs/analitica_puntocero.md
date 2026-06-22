# Analitica basica de Punto Cero

Fecha: 2026-06-21

## Objetivo

Registrar uso general del sitio con fines de investigacion y evaluacion del proyecto, sin Google Analytics, sin cookies invasivas y sin mostrar datos personales en curaduria.

## Tabla

La tabla se crea con:

`supabase/analytics_events.sql`

Campos:

- `id`
- `event_type`
- `point_id`
- `created_at`
- `session_id`
- `user_agent`

Eventos permitidos:

- `visit_home`
- `visit_map`
- `open_point`
- `play_audio`
- `submit_testimony`

## Privacidad

- No se usan cookies.
- `session_id` se guarda en `sessionStorage`, por lo que dura solo durante la pestana/sesion del navegador.
- No se registra nombre, correo, telefono ni contenido del testimonio.
- `user_agent` se guarda solo como dato tecnico opcional del navegador.
- En `curaduria.html` solo se muestran conteos agregados.

## Que registra cada evento

### visit_home

Se registra cuando alguien abre `index.html` y llega a la portada.

### visit_map

Se registra cuando la persona entra al mapa desde la portada.

### open_point

Se registra cuando se abre un punto sonoro del mapa, desde la lista, el mapa, ruta narrativa o enlace directo.

### play_audio

Se registra cuando:

- un audio nativo de HTML dispara evento `play`;
- una persona abre un enlace de escucha externo, como Spotify.

Limitacion tecnica: Spotify usa iframe externo y no expone al sitio el evento real de reproduccion dentro del reproductor embebido. Por eso el sitio registra la intencion de escucha cuando se abre el enlace externo o el audio nativo se reproduce.

### submit_testimony

Se registra solo despues de que `captura.html` guarda correctamente el audio y los metadatos en Supabase.

## Panel de estadisticas

`curaduria.html` muestra:

- Visitas totales.
- Visitas ultimos 30 dias.
- Puntos abiertos.
- Audios reproducidos.
- Testimonios recibidos.

Si el panel muestra error, revisar:

1. Que `supabase/analytics_events.sql` ya se ejecuto en Supabase SQL Editor.
2. Que el usuario autenticado sea `gvalenzuela@somoseduk.org`.
3. Que la funcion `public.is_testimony_admin()` reconozca ese correo.
4. Que RLS permita `SELECT` al admin autenticado.

## Seguridad

- `anon` solo puede insertar eventos con tipos permitidos.
- `anon` no puede leer la tabla.
- `authenticated` solo puede leer si `public.is_testimony_admin()` devuelve `true`.
- No se usa `service_role` en frontend.
