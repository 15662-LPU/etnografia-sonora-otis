# Cierre de fase: Frontend local para construccion etica de UDAN Corpus B

Fecha: 2026-06-29

## 1. Identificacion de la fase

- Proyecto: Punto Cero Acapulco.
- Tesis doctoral: Trabajo Social de la Emergencia.
- Corpus: Corpus B - testimonios ciudadanos.
- Herramienta creada: `scripts/corpus_b_gui.py`.
- Script base actualizado: `scripts/build_corpus_b_udan.py`.
- Commit tecnico: `6a675d7`.
- Estado: validado localmente.

## 2. Proposito de la herramienta

La interfaz local fue creada para facilitar la construccion de Unidades Documentales de Analisis Narrativo, UDAN, del Corpus B sin depender del uso constante de comandos en terminal. Su funcion es acompanar el flujo operativo de un caso piloto, conservar trazabilidad metodologica y reducir errores de manejo documental sin eliminar los controles eticos humanos.

La herramienta actua como apoyo local para preparar documentos de trabajo doctoral destinados a ATLAS.ti Web. No convierte automaticamente un testimonio en evidencia analitica: ordena el expediente, registra decisiones y bloquea pasos cuando faltan condiciones eticas minimas.

## 3. Alcance funcional

La herramienta permite:

- crear y verificar casos UDAN;
- registrar `submission_id`;
- registrar consentimiento;
- seleccionar y copiar audio local autorizado;
- seleccionar transcripcion preliminar, revisada y anonimizada;
- registrar revision etica;
- generar DOCX compatible con ATLAS.ti Web;
- validar el estado del caso;
- abrir carpetas locales del expediente;
- registrar acciones en `08_logs_metodologicos/log_metodologico.md`.

## 4. Restricciones eticas y tecnicas conservadas

La herramienta:

- no consulta Supabase;
- no lee `.env.local`;
- no descarga audios;
- no ejecuta Whisper automaticamente;
- no modifica `index.html`;
- no modifica `captura.html`;
- no modifica `curaduria.html`;
- no modifica SQL;
- no publica testimonios;
- no procesa Corpus B en masa;
- no sustituye la revision humana;
- no sube documentos automaticamente a ATLAS.ti Web.

Estas restricciones preservan la separacion entre recepcion temporal, resguardo institucional, preparacion documental local y analisis cualitativo.

## 5. Caso piloto validado

- ID: `PC-2026-B001-PILOTO`.
- Consentimiento: otorgado.
- Audio: registrado.
- Transcripcion anonimizada: registrada.
- Decision final: exportable.
- DOCX ATLAS.ti Web: generado.
- Importacion a ATLAS.ti Web: manual.

El caso piloto valida la ruta metodologica basica: testimonio ciudadano autorizado, audio local resguardado, transcripcion anonimizada, decision etica documentada y generacion de documento DOCX para analisis posterior.

## 6. Validaciones realizadas

Se ejecutaron las siguientes validaciones:

```powershell
python -m py_compile scripts\corpus_b_gui.py scripts\build_corpus_b_udan.py
python scripts\build_corpus_b_udan.py validate --root data_urv --id PC-2026-B001-PILOTO
git diff --check
git diff --cached --check
```

Resultado: no hubo errores. `git diff --check` solo mostro avisos LF/CRLF preexistentes en archivos ajenos a esta fase.

## 7. Decisiones humanas obligatorias

Siguen siendo responsabilidad del investigador:

- seleccionar el testimonio;
- confirmar consentimiento;
- descargar manualmente el audio autorizado;
- ejecutar Whisper local fuera del sistema;
- revisar transcripciones;
- anonimizar contenido;
- decidir revision etica final;
- generar exportacion solo si procede;
- importar manualmente a ATLAS.ti Web.

La GUI no reemplaza el juicio etico ni metodologico; solo ordena el flujo de trabajo local.

## 8. Relevancia metodologica para la tesis

Esta fase consolida un flujo local, etico y trazable para transformar testimonios ciudadanos en unidades documentales analizables dentro de una investigacion doctoral sobre Trabajo Social de la Emergencia. La herramienta permite sostener una cadena metodologica entre testimonio, consentimiento, resguardo, transcripcion, anonimizacion, revision etica y documento de analisis, sin automatizar decisiones sensibles ni comprometer la seguridad de los datos. De este modo, la produccion del corpus se mantiene alineada con criterios de cuidado, responsabilidad investigadora y trazabilidad academica.

## 9. Criterio de cierre

La fase se considera cerrada porque:

- la GUI funciona;
- el caso piloto valido correctamente;
- el DOCX fue generado;
- las restricciones eticas se conservaron;
- el commit tecnico fue creado localmente;
- no se realizo procesamiento masivo;
- no se toco produccion.

El siguiente paso metodologico es revisar manualmente el DOCX piloto, importar el documento a ATLAS.ti Web de forma controlada y documentar la primera experiencia de codificacion como parte de la validacion doctoral del corpus.
