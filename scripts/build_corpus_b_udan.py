#!/usr/bin/env python3
"""Construye una UDAN piloto local para Corpus B.

La herramienta trabaja solo con un caso autorizado por el investigador. No
conecta a Supabase, no lee .env.local, no descarga audios, no ejecuta Whisper y
no procesa el Corpus B completo.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_UDAN_ID = "PC-2026-B001-PILOTO"
VALID_DECISIONS = {"exportable", "requiere_anonimizacion", "pausar", "excluir"}
VALID_CONSENT = {"pendiente", "otorgado", "denegado", "rechazado", "ambiguo", "retirado"}

CASE_DIRECTORIES = [
    "01_audio_original_restringido",
    "02_consentimiento_restringido",
    "03_transcripcion_preliminar",
    "04_transcripcion_revisada",
    "05_transcripcion_anonimizada",
    "06_uda_docx_atlas_web",
    "07_revision_etica",
    "08_logs_metodologicos",
    "metadata",
]


class UdanError(RuntimeError):
    """Error controlado para la CLI."""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def display_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.name


def resolve_root(value: str) -> Path:
    root = Path(value)
    if not root.is_absolute():
        root = PROJECT_ROOT / root
    resolved = root.resolve()
    project = PROJECT_ROOT.resolve()
    if resolved != project and project not in resolved.parents:
        raise UdanError("--root debe estar dentro del repositorio local.")
    return resolved


def case_dir(root: Path, udan_id: str) -> Path:
    return root / "Corpus_B_testimonios_ciudadanos" / udan_id


def require_case(root: Path, udan_id: str) -> Path:
    target = case_dir(root, udan_id)
    if not target.exists():
        raise UdanError(f"No existe el caso {udan_id}. Ejecuta init-case primero.")
    return target


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise UdanError(f"No existe {display_path(path)}.")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], dry_run: bool = False) -> None:
    if dry_run:
        print(f"[dry-run] escribir JSON {display_path(path)}")
        return
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str, dry_run: bool = False) -> None:
    if dry_run:
        print(f"[dry-run] escribir archivo {display_path(path)}")
        return
    path.write_text(content, encoding="utf-8")


def append_log(target: Path, message: str, dry_run: bool = False) -> None:
    log_path = target / "08_logs_metodologicos" / "log_metodologico.md"
    line = f"\n- {now_iso()} - {message}\n"
    if dry_run:
        print(f"[dry-run] registrar log {display_path(log_path)}: {message}")
        return
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(line)


def metadata_path(target: Path) -> Path:
    return target / "metadata" / "metadata.json"


def state_path(target: Path) -> Path:
    return target / "metadata" / "estado_udan.json"


def ethics_path(target: Path) -> Path:
    return target / "07_revision_etica" / "revision_etica.json"


def read_case_files(target: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return load_json(metadata_path(target)), load_json(state_path(target)), load_json(ethics_path(target))


def save_case_files(
    target: Path,
    metadata: dict[str, Any],
    state: dict[str, Any],
    ethics: dict[str, Any],
    dry_run: bool = False,
) -> None:
    write_json(metadata_path(target), metadata, dry_run=dry_run)
    write_json(state_path(target), state, dry_run=dry_run)
    write_json(ethics_path(target), ethics, dry_run=dry_run)


def build_initial_metadata(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "id_udan": args.id,
        "id_expediente": args.id,
        "tipo_corpus": "B",
        "descripcion_corpus": "Corpus B - testimonios ciudadanos",
        "submission_id": args.submission_id,
        "fecha_creacion": now_iso(),
        "comunidad_zona_amplia": args.comunidad,
        "perfil_participante_no_identificativo": args.perfil_participante,
        "tipo_relato": args.tipo_relato,
        "duracion": args.duracion,
        "consentimiento": args.consentimiento,
        "estado_etico": "pendiente_revision",
        "decision_final": "pendiente",
        "estado_transcripcion": "pendiente",
        "estado_anonimizacion": "pendiente",
        "estado_docx_atlas_web": "pendiente",
        "restricciones_uso": "No publicar. No importar a ATLAS.ti Web hasta decision exportable.",
        "notas": (
            "Caso piloto local. No contiene audio descargado por la herramienta ni "
            "consulta automatica a Supabase."
        ),
    }


def build_initial_state(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "id_udan": args.id,
        "submission_id": args.submission_id,
        "audio": {
            "estado": "pendiente",
            "archivo": None,
            "registrado_at": None,
            "origen": "descarga_manual_autorizada_pendiente",
        },
        "consentimiento": {
            "estado": args.consentimiento,
            "actualizado_at": now_iso(),
            "notas": "Debe ser otorgado antes de decision exportable.",
        },
        "transcripcion_preliminar": {"estado": "pendiente", "archivo": None, "registrado_at": None},
        "transcripcion_revisada": {"estado": "pendiente", "archivo": None, "registrado_at": None},
        "transcripcion_anonimizada": {"estado": "pendiente", "archivo": None, "registrado_at": None},
        "revision_etica": {"estado": "pendiente", "decision": "pendiente", "reviewed_by": None},
        "docx_atlas_web": {"estado": "pendiente", "archivo": None, "generado_at": None},
        "limites": {
            "supabase_consultado": False,
            "audio_descargado_por_script": False,
            "whisper_ejecutado_por_script": False,
            "procesamiento_masivo": False,
        },
    }


def build_initial_ethics(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "id_udan": args.id,
        "submission_id": args.submission_id,
        "estado_revision": "pendiente",
        "decision_final": "pendiente",
        "reviewed_by": None,
        "reviewed_at": None,
        "notes": "",
        "requiere_revision_humana": True,
        "alertas": [],
        "criterios_bloqueo": [
            "consentimiento_no_otorgado",
            "transcripcion_anonimizada_ausente",
            "revision_etica_no_exportable",
        ],
    }


def render_log(args: argparse.Namespace) -> str:
    return "\n".join(
        [
            f"# Log metodologico - {args.id}",
            "",
            f"- {now_iso()} - Caso piloto Corpus B inicializado.",
            f"- Submission ID manual registrado: {args.submission_id}",
            "- Supabase no fue consultado por esta herramienta.",
            "- No se descargo audio por script.",
            "- No se ejecuto Whisper.",
            "",
        ]
    )


def render_readme(args: argparse.Namespace) -> str:
    return "\n".join(
        [
            f"# ATLAS.ti Web - {args.id}",
            "",
            "Esta carpeta recibira el DOCX final de la UDAN piloto.",
            "",
            "No colocar aqui audio, consentimiento firmado, transcripcion preliminar ni datos identificativos.",
            "",
            "El DOCX solo puede generarse cuando:",
            "",
            "- el consentimiento este marcado como otorgado;",
            "- exista transcripcion anonimizada verificada;",
            "- la revision etica tenga decision final exportable.",
            "",
        ]
    )


def command_init_case(args: argparse.Namespace) -> int:
    if args.id != DEFAULT_UDAN_ID and "PILOTO" not in args.id:
        raise UdanError("Esta herramienta solo debe usarse para un caso piloto Corpus B.")
    if args.consentimiento not in VALID_CONSENT:
        raise UdanError(f"Consentimiento invalido: {args.consentimiento}")

    root = resolve_root(args.root)
    target = case_dir(root, args.id)
    for relative in CASE_DIRECTORIES:
        folder = target / relative
        if args.dry_run:
            print(f"[dry-run] crear carpeta {display_path(folder)}")
        else:
            folder.mkdir(parents=True, exist_ok=True)

    metadata = build_initial_metadata(args)
    state = build_initial_state(args)
    ethics = build_initial_ethics(args)
    write_json(metadata_path(target), metadata, dry_run=args.dry_run)
    write_json(state_path(target), state, dry_run=args.dry_run)
    write_json(ethics_path(target), ethics, dry_run=args.dry_run)
    write_text(target / "08_logs_metodologicos" / "log_metodologico.md", render_log(args), dry_run=args.dry_run)
    write_text(
        target / "06_uda_docx_atlas_web" / "README_ATLAS_WEB.md",
        render_readme(args),
        dry_run=args.dry_run,
    )

    if args.dry_run:
        print("Dry-run: no se escribieron archivos.")
    else:
        print(f"Caso piloto inicializado: {display_path(target)}")
    return 0


def safe_source_file(path_value: str) -> Path:
    source = Path(path_value).expanduser()
    if not source.exists() or not source.is_file():
        raise UdanError("El archivo local indicado no existe o no es un archivo.")
    return source.resolve()


def copy_local_file(source: Path, destination: Path, dry_run: bool, overwrite: bool = False) -> None:
    if destination.exists() and not overwrite:
        raise UdanError(
            f"El archivo destino ya existe: {display_path(destination)}. "
            "Confirma sobrescritura desde el wizard o renombra el archivo."
        )
    if dry_run:
        print(f"[dry-run] copiar archivo local {source.name} -> {display_path(destination)}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def command_set_consent(args: argparse.Namespace) -> int:
    if args.consentimiento not in VALID_CONSENT:
        raise UdanError(f"Consentimiento invalido: {args.consentimiento}")
    root = resolve_root(args.root)
    target = require_case(root, args.id)
    metadata, state, ethics = read_case_files(target)
    metadata["consentimiento"] = args.consentimiento
    metadata["consentimiento_notas"] = args.notes
    state["consentimiento"] = {
        "estado": args.consentimiento,
        "actualizado_at": now_iso(),
        "notas": args.notes,
    }
    save_case_files(target, metadata, state, ethics, dry_run=args.dry_run)
    append_log(target, f"Consentimiento actualizado a {args.consentimiento}.", dry_run=args.dry_run)
    print(f"Consentimiento registrado: {args.consentimiento}")
    return 0


def command_attach_audio(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    target = require_case(root, args.id)
    source = safe_source_file(args.audio_path)
    destination = target / "01_audio_original_restringido" / source.name
    metadata, state, ethics = read_case_files(target)
    copy_local_file(source, destination, args.dry_run, overwrite=getattr(args, "overwrite", False))
    state["audio"] = {
        "estado": "registrado",
        "archivo": source.name,
        "registrado_at": now_iso(),
        "origen": "archivo_local_descargado_manualmente_por_investigador",
    }
    save_case_files(target, metadata, state, ethics, dry_run=args.dry_run)
    append_log(target, f"Audio manual autorizado registrado: {source.name}.", dry_run=args.dry_run)
    print(f"Audio registrado: {source.name}")
    return 0


def attach_transcript(
    args: argparse.Namespace,
    folder: str,
    filename: str,
    state_key: str,
    metadata_status: dict[str, str],
) -> int:
    root = resolve_root(args.root)
    target = require_case(root, args.id)
    source = safe_source_file(args.transcript_path)
    destination = target / folder / filename
    metadata, state, ethics = read_case_files(target)
    copy_local_file(source, destination, args.dry_run, overwrite=getattr(args, "overwrite", False))
    state[state_key] = {
        "estado": "registrada",
        "archivo": filename,
        "registrado_at": now_iso(),
        "origen": "archivo_local_preparado_por_investigador",
    }
    metadata.update(metadata_status)
    save_case_files(target, metadata, state, ethics, dry_run=args.dry_run)
    append_log(target, f"{state_key} registrada desde archivo local: {source.name}.", dry_run=args.dry_run)
    print(f"{state_key} registrada: {filename}")
    return 0


def command_attach_preliminary(args: argparse.Namespace) -> int:
    return attach_transcript(
        args,
        "03_transcripcion_preliminar",
        "TRANSCRIPCION_PRELIMINAR.txt",
        "transcripcion_preliminar",
        {"estado_transcripcion": "preliminar_registrada"},
    )


def command_attach_reviewed(args: argparse.Namespace) -> int:
    return attach_transcript(
        args,
        "04_transcripcion_revisada",
        "TRANSCRIPCION_REVISADA.txt",
        "transcripcion_revisada",
        {"estado_transcripcion": "revisada"},
    )


def command_attach_anonymized(args: argparse.Namespace) -> int:
    return attach_transcript(
        args,
        "05_transcripcion_anonimizada",
        "TRANSCRIPCION_ANONIMIZADA_VERIFICADA.txt",
        "transcripcion_anonimizada",
        {"estado_transcripcion": "anonimizada_verificada", "estado_anonimizacion": "completa"},
    )


def anonymized_transcript_path(target: Path) -> Path:
    return target / "05_transcripcion_anonimizada" / "TRANSCRIPCION_ANONIMIZADA_VERIFICADA.txt"


def consent_is_granted(metadata: dict[str, Any], state: dict[str, Any]) -> bool:
    return metadata.get("consentimiento") == "otorgado" and state.get("consentimiento", {}).get("estado") == "otorgado"


def command_ethics_review(args: argparse.Namespace) -> int:
    if args.decision not in VALID_DECISIONS:
        raise UdanError(f"Decision invalida: {args.decision}")
    root = resolve_root(args.root)
    target = require_case(root, args.id)
    metadata, state, ethics = read_case_files(target)
    if args.decision == "exportable":
        if not anonymized_transcript_path(target).exists():
            raise UdanError("No se permite exportable: falta transcripcion anonimizada verificada.")
        if not consent_is_granted(metadata, state):
            raise UdanError("No se permite exportable: consentimiento debe estar marcado como otorgado.")

    metadata["estado_etico"] = "revisado"
    metadata["decision_final"] = args.decision
    ethics.update(
        {
            "estado_revision": "revisada",
            "decision_final": args.decision,
            "reviewed_by": args.reviewed_by,
            "reviewed_at": now_iso(),
            "notes": args.notes,
            "requiere_revision_humana": True,
        }
    )
    state["revision_etica"] = {
        "estado": "revisada",
        "decision": args.decision,
        "reviewed_by": args.reviewed_by,
        "reviewed_at": ethics["reviewed_at"],
    }
    save_case_files(target, metadata, state, ethics, dry_run=args.dry_run)
    append_log(target, f"Revision etica registrada con decision {args.decision}.", dry_run=args.dry_run)
    print(f"Decision etica registrada: {args.decision}")
    return 0


def docx_paragraph(text: str) -> str:
    escaped = escape(text)
    preserve = ' xml:space="preserve"' if text.startswith(" ") or text.endswith(" ") else ""
    return f"<w:p><w:r><w:t{preserve}>{escaped}</w:t></w:r></w:p>"


def write_docx(path: Path, lines: list[str], dry_run: bool, overwrite: bool = False) -> None:
    if path.exists() and not overwrite:
        raise UdanError(
            f"El DOCX ya existe: {display_path(path)}. "
            "Confirma sobrescritura desde el wizard o usa una version nueva."
        )
    if dry_run:
        print(f"[dry-run] escribir DOCX {display_path(path)}")
        return
    document_body = "".join(docx_paragraph(line) for line in lines)
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{document_body}<w:sectPr><w:pgSz w:w=\"12240\" w:h=\"15840\"/>"
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
        'w:header="720" w:footer="720" w:gutter="0"/></w:sectPr></w:body></w:document>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    package_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>'
        "</Relationships>"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types)
        docx.writestr("_rels/.rels", package_rels)
        docx.writestr("word/document.xml", document_xml)


def render_docx_lines(metadata: dict[str, Any], state: dict[str, Any], ethics: dict[str, Any], transcript: str) -> list[str]:
    return [
        f"UDAN Corpus B - {metadata['id_udan']}",
        "",
        "PORTADA",
        f"ID de la UDAN: {metadata['id_udan']}",
        "Tipo de corpus: Corpus B - testimonios ciudadanos",
        f"submission_id: {metadata['submission_id']}",
        f"Fecha de construccion: {now_iso()}",
        f"Comunidad o zona amplia: {metadata.get('comunidad_zona_amplia', 'pendiente')}",
        f"Perfil participante no identificativo: {metadata.get('perfil_participante_no_identificativo', 'pendiente')}",
        f"Tipo de relato: {metadata.get('tipo_relato', 'pendiente')}",
        f"Duracion: {metadata.get('duracion', 'pendiente')}",
        f"Consentimiento: {metadata.get('consentimiento', 'pendiente')}",
        f"Estado etico: {metadata.get('estado_etico', 'pendiente')}",
        f"Decision final: {ethics.get('decision_final', 'pendiente')}",
        "",
        "SECCION 1. Contexto documental",
        "Testimonio ciudadano preparado como caso piloto Corpus B.",
        "El audio original se conserva fuera de ATLAS.ti Web en resguardo restringido.",
        "Este documento contiene solo la version verificada y anonimizada para analisis.",
        "",
        "SECCION 2. Transcripcion verificada y anonimizada",
        transcript.strip() or "[TRANSCRIPCION_ANONIMIZADA_VACIA]",
        "",
        "SECCION 3. Observaciones metodologicas",
        "No contiene nombre real, telefono, domicilio exacto, consentimiento firmado ni audio.",
        "No incluye transcripcion preliminar.",
        f"Notas de revision etica: {ethics.get('notes', '')}",
        "",
        "SECCION 4. Espacio para memos del investigador",
        "[Agregar memos dentro de ATLAS.ti Web durante el analisis.]",
        "",
        "SECCION 5. Control documental",
        "Version: v4_docx_atlas_web",
        f"Fecha de revision: {ethics.get('reviewed_at', 'pendiente')}",
        f"Responsable: {ethics.get('reviewed_by', 'pendiente')}",
        f"Audio registrado: {state.get('audio', {}).get('archivo') or 'pendiente'}",
        f"Transcripcion anonimizada: {state.get('transcripcion_anonimizada', {}).get('archivo') or 'pendiente'}",
        "",
    ]


def command_build_docx(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    target = require_case(root, args.id)
    metadata, state, ethics = read_case_files(target)
    if ethics.get("decision_final") != "exportable":
        raise UdanError("No se puede generar DOCX: decision final no es exportable.")
    if not consent_is_granted(metadata, state):
        raise UdanError("No se puede generar DOCX: consentimiento no esta otorgado.")
    transcript_path = anonymized_transcript_path(target)
    if not transcript_path.exists():
        raise UdanError("No se puede generar DOCX: falta transcripcion anonimizada verificada.")

    transcript = transcript_path.read_text(encoding="utf-8")
    docx_path = target / "06_uda_docx_atlas_web" / f"{args.id}_ATLAS_WEB.docx"
    write_docx(
        docx_path,
        render_docx_lines(metadata, state, ethics, transcript),
        args.dry_run,
        overwrite=getattr(args, "overwrite", False),
    )

    metadata["estado_docx_atlas_web"] = "generado"
    state["docx_atlas_web"] = {
        "estado": "generado",
        "archivo": docx_path.name,
        "generado_at": now_iso(),
    }
    save_case_files(target, metadata, state, ethics, dry_run=args.dry_run)
    append_log(target, f"DOCX ATLAS.ti Web generado: {docx_path.name}.", dry_run=args.dry_run)
    print(f"DOCX generado: {display_path(docx_path)}")
    return 0


def prompt_text(label: str, default: str | None = None, required: bool = True) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        value = input(f"{label}{suffix}: ").strip()
        if not value and default is not None:
            return default
        if value or not required:
            return value
        print("Este campo es obligatorio.")


def prompt_choice(label: str, choices: list[str], default: str | None = None) -> str:
    rendered = "/".join(choices)
    while True:
        value = prompt_text(f"{label} ({rendered})", default=default, required=True)
        if value in choices:
            return value
        print(f"Opcion invalida. Usa una de: {rendered}")


def prompt_yes_no(label: str, default: bool = False) -> bool:
    default_text = "s" if default else "n"
    value = prompt_choice(label, ["s", "n"], default=default_text)
    return value == "s"


def print_whisper_instructions() -> None:
    print("")
    print("Transcripcion preliminar pendiente.")
    print("Genera la transcripcion localmente, por ejemplo:")
    print("  python -m whisper RUTA_AUDIO_LOCAL --language Spanish --output_format txt")
    print("No uses servicios externos para voces ciudadanas.")
    print("")


def wizard_dry_run(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    target = case_dir(root, args.id)
    print("Wizard Corpus B UDAN - dry-run")
    print(f"Caso objetivo: {display_path(target)}")
    print("No se haran preguntas interactivas y no se escribiran archivos.")
    print("Pasos previstos:")
    steps = [
        "verificar o crear caso piloto",
        "registrar submission_id manual",
        "confirmar consentimiento",
        "detener flujo si consentimiento no es otorgado",
        "solicitar audio local descargado manualmente",
        "copiar audio al expediente con confirmacion si existe destino",
        "registrar transcripcion preliminar o mostrar instrucciones Whisper local",
        "registrar transcripcion revisada",
        "registrar transcripcion anonimizada",
        "intentar revision etica local si la integracion esta disponible",
        "solicitar decision etica final",
        "generar DOCX solo si decision es exportable",
        "validar caso",
        "mostrar ruta final del DOCX si existe",
    ]
    for index, step in enumerate(steps, start=1):
        print(f"{index}. {step}")
    return 0


def init_case_from_wizard(root: Path, target: Path, args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if target.exists():
        print(f"Caso existente: {display_path(target)}")
        return read_case_files(target)

    submission_id = prompt_text("submission_id seleccionado manualmente")
    comunidad = prompt_text("Comunidad o zona amplia", default="pendiente")
    perfil = prompt_text("Perfil participante no identificativo", default="pendiente")
    tipo_relato = prompt_text("Tipo de relato", default="pendiente")
    duracion = prompt_text("Duracion", default="pendiente")
    init_args = argparse.Namespace(
        root=args.root,
        id=args.id,
        submission_id=submission_id,
        comunidad=comunidad,
        perfil_participante=perfil,
        tipo_relato=tipo_relato,
        duracion=duracion,
        consentimiento="pendiente",
        dry_run=False,
    )
    command_init_case(init_args)
    append_log(target, "Wizard creo el caso piloto.")
    return read_case_files(target)


def update_submission_id_from_wizard(target: Path, metadata: dict[str, Any], state: dict[str, Any], ethics: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    current = str(metadata.get("submission_id") or "")
    if current and current != "SUBMISSION_ID_MANUAL":
        if not prompt_yes_no(f"submission_id actual: {current}. Deseas cambiarlo?", default=False):
            return metadata, state, ethics
    new_submission_id = prompt_text("submission_id seleccionado manualmente", default=current or None)
    metadata["submission_id"] = new_submission_id
    state["submission_id"] = new_submission_id
    ethics["submission_id"] = new_submission_id
    save_case_files(target, metadata, state, ethics)
    append_log(target, "Wizard registro o actualizo submission_id manual.")
    return metadata, state, ethics


def wizard_copy_file(source_value: str, destination: Path, dry_run: bool = False) -> bool:
    source = safe_source_file(source_value)
    overwrite = False
    if destination.exists():
        overwrite = prompt_yes_no(
            f"Ya existe {display_path(destination)}. Sobrescribir?",
            default=False,
        )
        if not overwrite:
            print("Copia omitida para no sobrescribir.")
            return False
    copy_local_file(source, destination, dry_run=dry_run, overwrite=overwrite)
    return True


def wizard_attach_audio(target: Path, metadata: dict[str, Any], state: dict[str, Any], ethics: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if state.get("audio", {}).get("estado") == "registrado":
        if not prompt_yes_no("Ya hay audio registrado. Deseas registrar otro archivo local?", default=False):
            return metadata, state, ethics
    audio_path = prompt_text("Ruta local del audio descargado manualmente", required=False)
    if not audio_path:
        append_log(target, "Wizard dejo audio pendiente por decision humana.")
        print("Audio queda pendiente.")
        return metadata, state, ethics
    source = safe_source_file(audio_path)
    destination = target / "01_audio_original_restringido" / source.name
    if wizard_copy_file(audio_path, destination):
        state["audio"] = {
            "estado": "registrado",
            "archivo": source.name,
            "registrado_at": now_iso(),
            "origen": "archivo_local_descargado_manualmente_por_investigador",
        }
        save_case_files(target, metadata, state, ethics)
        append_log(target, f"Wizard registro audio manual autorizado: {source.name}.")
    return metadata, state, ethics


def wizard_attach_transcript(
    target: Path,
    metadata: dict[str, Any],
    state: dict[str, Any],
    ethics: dict[str, Any],
    prompt_label: str,
    folder: str,
    filename: str,
    state_key: str,
    metadata_status: dict[str, str],
    required: bool,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    transcript_path = prompt_text(prompt_label, required=required)
    if not transcript_path:
        append_log(target, f"Wizard dejo {state_key} pendiente.")
        return metadata, state, ethics
    source = safe_source_file(transcript_path)
    destination = target / folder / filename
    if wizard_copy_file(transcript_path, destination):
        state[state_key] = {
            "estado": "registrada",
            "archivo": filename,
            "registrado_at": now_iso(),
            "origen": "archivo_local_preparado_por_investigador",
        }
        metadata.update(metadata_status)
        save_case_files(target, metadata, state, ethics)
        append_log(target, f"Wizard registro {state_key}: {source.name}.")
    return metadata, state, ethics


def run_local_ethics_if_available(root: Path, target: Path, args: argparse.Namespace) -> None:
    ethical_script = PROJECT_ROOT / "scripts" / "ethical_alerts.py"
    transcript = anonymized_transcript_path(target)
    if not ethical_script.exists() or not transcript.exists():
        append_log(target, "Wizard no ejecuto revision etica automatica: integracion o transcripcion ausente.")
        return
    if not prompt_yes_no("Ejecutar revision etica local sobre transcripcion anonimizada?", default=True):
        append_log(target, "Wizard omitio revision etica automatica por decision humana.")
        return
    relative_input = "05_transcripcion_anonimizada/TRANSCRIPCION_ANONIMIZADA_VERIFICADA.txt"
    completed = subprocess.run(
        [
            sys.executable,
            str(ethical_script),
            "scan",
            "--root",
            str(root),
            "--id",
            args.id,
            "--input",
            relative_input,
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode == 0:
        append_log(target, "Wizard ejecuto revision etica local mediante ethical_alerts.py.")
        print("Revision etica local ejecutada.")
    else:
        append_log(
            target,
            "Wizard no pudo ejecutar ethical_alerts.py; queda pendiente revision etica manual.",
        )
        print("No se pudo ejecutar ethical_alerts.py para este caso. Queda pendiente revision manual.")


def command_wizard(args: argparse.Namespace) -> int:
    if args.dry_run:
        return wizard_dry_run(args)

    root = resolve_root(args.root)
    target = case_dir(root, args.id)
    print("Wizard Corpus B UDAN")
    print("Este asistente trabaja con un solo caso piloto y no consulta Supabase.")
    metadata, state, ethics = init_case_from_wizard(root, target, args)
    metadata, state, ethics = update_submission_id_from_wizard(target, metadata, state, ethics)

    current_consent = str(metadata.get("consentimiento") or "pendiente")
    if current_consent not in {"otorgado", "pendiente", "ambiguo", "rechazado"}:
        current_consent = "pendiente"
    consent = prompt_choice(
        "Confirmar consentimiento",
        ["otorgado", "pendiente", "ambiguo", "rechazado"],
        default=current_consent,
    )
    consent_args = argparse.Namespace(
        root=args.root,
        id=args.id,
        consentimiento=consent,
        notes="Registrado mediante wizard Corpus B.",
        dry_run=False,
    )
    command_set_consent(consent_args)
    metadata, state, ethics = read_case_files(target)
    if consent != "otorgado":
        append_log(target, f"Wizard detenido: consentimiento {consent}.")
        print("Flujo detenido: consentimiento no otorgado.")
        return command_validate(argparse.Namespace(root=args.root, id=args.id))

    metadata, state, ethics = wizard_attach_audio(target, metadata, state, ethics)

    has_preliminary = prompt_yes_no("Existe transcripcion preliminar?", default=False)
    if has_preliminary:
        metadata, state, ethics = wizard_attach_transcript(
            target,
            metadata,
            state,
            ethics,
            "Ruta de TRANSCRIPCION_PRELIMINAR.txt",
            "03_transcripcion_preliminar",
            "TRANSCRIPCION_PRELIMINAR.txt",
            "transcripcion_preliminar",
            {"estado_transcripcion": "preliminar_registrada"},
            required=True,
        )
    else:
        print_whisper_instructions()
        append_log(target, "Wizard mostro instrucciones para Whisper local; no ejecuto Whisper.")

    metadata, state, ethics = wizard_attach_transcript(
        target,
        metadata,
        state,
        ethics,
        "Ruta de TRANSCRIPCION_REVISADA.txt",
        "04_transcripcion_revisada",
        "TRANSCRIPCION_REVISADA.txt",
        "transcripcion_revisada",
        {"estado_transcripcion": "revisada"},
        required=True,
    )
    metadata, state, ethics = wizard_attach_transcript(
        target,
        metadata,
        state,
        ethics,
        "Ruta de TRANSCRIPCION_ANONIMIZADA.txt",
        "05_transcripcion_anonimizada",
        "TRANSCRIPCION_ANONIMIZADA_VERIFICADA.txt",
        "transcripcion_anonimizada",
        {"estado_transcripcion": "anonimizada_verificada", "estado_anonimizacion": "completa"},
        required=True,
    )

    run_local_ethics_if_available(root, target, args)

    decision = prompt_choice(
        "Decision etica final",
        ["exportable", "requiere_anonimizacion", "pausar", "excluir"],
        default="pausar",
    )
    reviewed_by = prompt_text("Responsable de revision", default="investigador_principal")
    notes = prompt_text("Notas de revision etica", default="Revision mediante wizard Corpus B.", required=False)
    command_ethics_review(
        argparse.Namespace(
            root=args.root,
            id=args.id,
            decision=decision,
            reviewed_by=reviewed_by,
            notes=notes,
            dry_run=False,
        )
    )

    docx_path = target / "06_uda_docx_atlas_web" / f"{args.id}_ATLAS_WEB.docx"
    if decision == "exportable":
        overwrite = False
        if docx_path.exists():
            overwrite = prompt_yes_no(f"Ya existe {display_path(docx_path)}. Sobrescribir?", default=False)
        command_build_docx(
            argparse.Namespace(root=args.root, id=args.id, dry_run=False, overwrite=overwrite)
        )
    else:
        append_log(target, f"Wizard no genero DOCX porque decision final fue {decision}.")
        print("DOCX no generado: decision final no exportable.")

    result = command_validate(argparse.Namespace(root=args.root, id=args.id))
    if docx_path.exists():
        print(f"Ruta final DOCX: {display_path(docx_path)}")
    else:
        print("DOCX final pendiente.")
    return result


def validate_case(target: Path) -> list[str]:
    errors: list[str] = []
    for relative in CASE_DIRECTORIES:
        if not (target / relative).exists():
            errors.append(f"Falta carpeta {relative}")
    for required in [metadata_path(target), state_path(target), ethics_path(target)]:
        if not required.exists():
            errors.append(f"Falta archivo {display_path(required)}")
    if errors:
        return errors

    metadata, state, ethics = read_case_files(target)
    if not metadata.get("submission_id"):
        errors.append("metadata.json no tiene submission_id")
    if "consentimiento" not in metadata:
        errors.append("metadata.json no tiene campo consentimiento")
    if state.get("audio", {}).get("estado") not in {"pendiente", "registrado"}:
        errors.append("audio debe estar registrado o pendiente")
    anonymized_exists = anonymized_transcript_path(target).exists()
    docx_exists = (target / "06_uda_docx_atlas_web" / f"{metadata.get('id_udan')}_ATLAS_WEB.docx").exists()
    decision = ethics.get("decision_final")
    if decision == "exportable":
        if not anonymized_exists:
            errors.append("decision exportable sin transcripcion anonimizada")
        if not consent_is_granted(metadata, state):
            errors.append("decision exportable sin consentimiento otorgado")
        if not docx_exists:
            errors.append("decision exportable sin DOCX generado")
    if docx_exists and not anonymized_exists:
        errors.append("existe DOCX sin transcripcion anonimizada")
    if docx_exists and not consent_is_granted(metadata, state):
        errors.append("existe DOCX sin consentimiento otorgado")
    if docx_exists and decision != "exportable":
        errors.append("existe DOCX sin decision final exportable")
    if ethics.get("estado_revision") not in {"pendiente", "revisada"}:
        errors.append("revision_etica.json tiene estado_revision invalido")
    return errors


def command_validate(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    target = require_case(root, args.id)
    errors = validate_case(target)
    if errors:
        print("Validacion con errores:")
        for error in errors:
            print(f"- {error}")
        return 1
    metadata, state, ethics = read_case_files(target)
    print(f"Caso valido: {metadata.get('id_udan')}")
    print(f"Consentimiento: {metadata.get('consentimiento')}")
    print(f"Audio: {state.get('audio', {}).get('estado')}")
    print(f"Transcripcion anonimizada: {state.get('transcripcion_anonimizada', {}).get('estado')}")
    print(f"Decision final: {ethics.get('decision_final')}")
    print(f"DOCX ATLAS.ti Web: {state.get('docx_atlas_web', {}).get('estado')}")
    return 0


def add_common_case_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", default="data_urv")
    parser.add_argument("--id", default=DEFAULT_UDAN_ID)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gestiona una UDAN piloto local Corpus B.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_case = subparsers.add_parser("init-case")
    add_common_case_args(init_case)
    init_case.add_argument("--submission-id", required=True)
    init_case.add_argument("--comunidad", default="pendiente")
    init_case.add_argument("--perfil-participante", default="pendiente")
    init_case.add_argument("--tipo-relato", default="pendiente")
    init_case.add_argument("--duracion", default="pendiente")
    init_case.add_argument("--consentimiento", default="pendiente", choices=sorted(VALID_CONSENT))
    init_case.add_argument("--dry-run", action="store_true")
    init_case.set_defaults(func=command_init_case)

    set_consent = subparsers.add_parser("set-consent")
    add_common_case_args(set_consent)
    set_consent.add_argument("--consentimiento", required=True, choices=sorted(VALID_CONSENT))
    set_consent.add_argument("--notes", default="")
    set_consent.add_argument("--dry-run", action="store_true")
    set_consent.set_defaults(func=command_set_consent)

    attach_audio = subparsers.add_parser("attach-audio")
    add_common_case_args(attach_audio)
    attach_audio.add_argument("--audio-path", required=True)
    attach_audio.add_argument("--dry-run", action="store_true")
    attach_audio.add_argument("--overwrite", action="store_true")
    attach_audio.set_defaults(func=command_attach_audio)

    attach_preliminary = subparsers.add_parser("attach-preliminary-transcript")
    add_common_case_args(attach_preliminary)
    attach_preliminary.add_argument("--transcript-path", required=True)
    attach_preliminary.add_argument("--dry-run", action="store_true")
    attach_preliminary.add_argument("--overwrite", action="store_true")
    attach_preliminary.set_defaults(func=command_attach_preliminary)

    attach_reviewed = subparsers.add_parser("attach-reviewed-transcript")
    add_common_case_args(attach_reviewed)
    attach_reviewed.add_argument("--transcript-path", required=True)
    attach_reviewed.add_argument("--dry-run", action="store_true")
    attach_reviewed.add_argument("--overwrite", action="store_true")
    attach_reviewed.set_defaults(func=command_attach_reviewed)

    attach_anonymized = subparsers.add_parser("attach-anonymized-transcript")
    add_common_case_args(attach_anonymized)
    attach_anonymized.add_argument("--transcript-path", required=True)
    attach_anonymized.add_argument("--dry-run", action="store_true")
    attach_anonymized.add_argument("--overwrite", action="store_true")
    attach_anonymized.set_defaults(func=command_attach_anonymized)

    ethics = subparsers.add_parser("ethics-review")
    add_common_case_args(ethics)
    ethics.add_argument("--decision", required=True, choices=sorted(VALID_DECISIONS))
    ethics.add_argument("--reviewed-by", required=True)
    ethics.add_argument("--notes", default="")
    ethics.add_argument("--dry-run", action="store_true")
    ethics.set_defaults(func=command_ethics_review)

    build_docx = subparsers.add_parser("build-docx")
    add_common_case_args(build_docx)
    build_docx.add_argument("--dry-run", action="store_true")
    build_docx.add_argument("--overwrite", action="store_true")
    build_docx.set_defaults(func=command_build_docx)

    validate = subparsers.add_parser("validate")
    add_common_case_args(validate)
    validate.set_defaults(func=command_validate)

    wizard = subparsers.add_parser("wizard")
    add_common_case_args(wizard)
    wizard.add_argument("--dry-run", action="store_true")
    wizard.set_defaults(func=command_wizard)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except UdanError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
