#!/usr/bin/env python3
"""Interfaz local para construir una UDAN piloto del Corpus B.

La GUI es un frente local de scripts/build_corpus_b_udan.py. No consulta
Supabase, no lee .env.local, no descarga audios, no ejecuta Whisper y no toca
archivos de produccion.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable

import build_corpus_b_udan as backend


PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUDIO_TYPES = [
    ("Audio compatible", "*.wav *.mp3 *.m4a *.ogg *.webm"),
    ("WAV", "*.wav"),
    ("MP3", "*.mp3"),
    ("M4A", "*.m4a"),
    ("OGG", "*.ogg"),
    ("WEBM", "*.webm"),
]
TXT_TYPES = [("Texto TXT", "*.txt")]


class CorpusBGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Punto Cero - Piloto Corpus B UDAN")
        self.geometry("980x720")
        self.minsize(880, 640)

        self.root_var = tk.StringVar(value="data_urv")
        self.id_var = tk.StringVar(value=backend.DEFAULT_UDAN_ID)
        self.submission_var = tk.StringVar(value="")
        self.consent_var = tk.StringVar(value="pendiente")
        self.decision_var = tk.StringVar(value="pausar")
        self.reviewed_by_var = tk.StringVar(value="investigador_principal")
        self.notes_var = tk.StringVar(value="Piloto metodologico Corpus B")
        self.docx_path_var = tk.StringVar(value="DOCX pendiente")

        self.status_labels: dict[str, tk.StringVar] = {}
        self.build_ui()
        self.refresh_status(silent=True)

    def build_ui(self) -> None:
        container = ttk.Frame(self, padding=14)
        container.pack(fill=tk.BOTH, expand=True)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(5, weight=1)

        header = ttk.Label(
            container,
            text="Construccion local de UDAN Corpus B para ATLAS.ti Web",
            font=("Segoe UI", 14, "bold"),
        )
        header.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        self.build_case_section(container).grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=6)
        self.build_consent_section(container).grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=6)
        self.build_files_section(container).grid(row=2, column=0, sticky="nsew", padx=(0, 8), pady=6)
        self.build_ethics_section(container).grid(row=2, column=1, sticky="nsew", padx=(8, 0), pady=6)
        self.build_docx_section(container).grid(row=3, column=0, columnspan=2, sticky="nsew", pady=6)
        self.build_status_section(container).grid(row=4, column=0, columnspan=2, sticky="nsew", pady=6)
        self.build_log_section(container).grid(row=5, column=0, columnspan=2, sticky="nsew", pady=(6, 0))

    def labelled_entry(self, parent: ttk.Frame, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=3)

    def build_case_section(self, parent: ttk.Frame) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text="1. Seleccion del caso", padding=10)
        frame.columnconfigure(1, weight=1)
        self.labelled_entry(frame, 0, "Raiz local", self.root_var)
        self.labelled_entry(frame, 1, "ID UDAN", self.id_var)
        self.labelled_entry(frame, 2, "submission_id", self.submission_var)
        ttk.Button(frame, text="Crear / verificar caso", command=self.create_or_verify_case).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )
        return frame

    def build_consent_section(self, parent: ttk.Frame) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text="2. Consentimiento", padding=10)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Estado").grid(row=0, column=0, sticky="w", pady=3)
        ttk.Combobox(
            frame,
            textvariable=self.consent_var,
            values=["otorgado", "pendiente", "ambiguo", "rechazado"],
            state="readonly",
        ).grid(row=0, column=1, sticky="ew", pady=3)
        ttk.Button(frame, text="Registrar consentimiento", command=self.register_consent).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )
        return frame

    def build_files_section(self, parent: ttk.Frame) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text="3. Audio y transcripciones", padding=10)
        frame.columnconfigure(0, weight=1)
        buttons = [
            ("Seleccionar audio local", self.select_audio),
            ("Seleccionar transcripcion preliminar", self.select_preliminary),
            ("Seleccionar transcripcion revisada", self.select_reviewed),
            ("Seleccionar transcripcion anonimizada", self.select_anonymized),
        ]
        for row, (text, command) in enumerate(buttons):
            ttk.Button(frame, text=text, command=command).grid(row=row, column=0, sticky="ew", pady=4)
        ttk.Label(
            frame,
            text="La GUI copia archivos locales. No descarga audios ni ejecuta Whisper.",
            foreground="#555555",
        ).grid(row=len(buttons), column=0, sticky="w", pady=(8, 0))
        return frame

    def build_ethics_section(self, parent: ttk.Frame) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text="4. Revision etica", padding=10)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Decision").grid(row=0, column=0, sticky="w", pady=3)
        ttk.Combobox(
            frame,
            textvariable=self.decision_var,
            values=["exportable", "requiere_anonimizacion", "pausar", "excluir"],
            state="readonly",
        ).grid(row=0, column=1, sticky="ew", pady=3)
        self.labelled_entry(frame, 1, "Responsable", self.reviewed_by_var)
        ttk.Label(frame, text="Notas").grid(row=2, column=0, sticky="nw", pady=3)
        ttk.Entry(frame, textvariable=self.notes_var).grid(row=2, column=1, sticky="ew", pady=3)
        ttk.Button(frame, text="Registrar revision etica", command=self.register_ethics).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )
        return frame

    def build_docx_section(self, parent: ttk.Frame) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text="5. DOCX ATLAS.ti Web y carpetas", padding=10)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        self.build_docx_button = ttk.Button(
            frame,
            text="Generar DOCX para ATLAS.ti Web",
            command=self.build_docx,
        )
        self.build_docx_button.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=3)
        ttk.Button(frame, text="Validar caso", command=self.validate_case).grid(
            row=0, column=1, sticky="ew", padx=(6, 0), pady=3
        )
        ttk.Button(frame, text="Abrir carpeta del caso", command=self.open_case_folder).grid(
            row=1, column=0, sticky="ew", padx=(0, 6), pady=3
        )
        ttk.Button(frame, text="Abrir carpeta DOCX ATLAS.ti Web", command=self.open_docx_folder).grid(
            row=1, column=1, sticky="ew", padx=(6, 0), pady=3
        )
        ttk.Label(frame, textvariable=self.docx_path_var).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )
        return frame

    def build_status_section(self, parent: ttk.Frame) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text="6. Estado del caso", padding=10)
        for index, key in enumerate(
            [
                "consentimiento",
                "audio",
                "transcripcion_preliminar",
                "transcripcion_revisada",
                "transcripcion_anonimizada",
                "revision_etica",
                "docx_atlas_web",
            ]
        ):
            var = tk.StringVar(value="pendiente")
            self.status_labels[key] = var
            ttk.Label(frame, text=key.replace("_", " ").title()).grid(
                row=index // 2, column=(index % 2) * 2, sticky="w", padx=(0, 6), pady=3
            )
            ttk.Label(frame, textvariable=var, font=("Segoe UI", 9, "bold")).grid(
                row=index // 2, column=(index % 2) * 2 + 1, sticky="w", padx=(0, 24), pady=3
            )
        return frame

    def build_log_section(self, parent: ttk.Frame) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text="Registro de acciones de esta sesion", padding=10)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        self.output = tk.Text(frame, height=8, wrap="word")
        self.output.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(frame, command=self.output.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.output.configure(yscrollcommand=scrollbar.set)
        self.log("Interfaz local lista. No conecta a Supabase ni lee .env.local.")
        return frame

    def log(self, message: str) -> None:
        self.output.insert(tk.END, f"- {message}\n")
        self.output.see(tk.END)

    def root_path(self) -> Path:
        return backend.resolve_root(self.root_var.get().strip() or "data_urv")

    def case_path(self) -> Path:
        return backend.case_dir(self.root_path(), self.id_var.get().strip() or backend.DEFAULT_UDAN_ID)

    def docx_path(self) -> Path:
        case = self.case_path()
        udan_id = self.id_var.get().strip() or backend.DEFAULT_UDAN_ID
        return case / "06_uda_docx_atlas_web" / f"{udan_id}_ATLAS_WEB.docx"

    def run_backend(self, func: Callable[[Any], int], args: argparse.Namespace) -> int:
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            result = func(args)
        return result

    def show_error(self, exc: Exception) -> None:
        messagebox.showerror("Punto Cero Corpus B", str(exc))
        self.log(f"Error: {exc}")

    def refresh_status(self, silent: bool = False) -> None:
        try:
            target = self.case_path()
            if not target.exists():
                for var in self.status_labels.values():
                    var.set("pendiente")
                self.docx_path_var.set("DOCX pendiente")
                self.build_docx_button.state(["disabled"])
                return
            metadata, state, ethics = backend.read_case_files(target)
            self.submission_var.set(str(metadata.get("submission_id") or ""))
            consent = str(metadata.get("consentimiento") or "pendiente")
            if consent in {"otorgado", "pendiente", "ambiguo", "rechazado"}:
                self.consent_var.set(consent)
            self.status_labels["consentimiento"].set(consent)
            self.status_labels["audio"].set(str(state.get("audio", {}).get("estado") or "pendiente"))
            self.status_labels["transcripcion_preliminar"].set(
                str(state.get("transcripcion_preliminar", {}).get("estado") or "pendiente")
            )
            self.status_labels["transcripcion_revisada"].set(
                str(state.get("transcripcion_revisada", {}).get("estado") or "pendiente")
            )
            self.status_labels["transcripcion_anonimizada"].set(
                str(state.get("transcripcion_anonimizada", {}).get("estado") or "pendiente")
            )
            self.status_labels["revision_etica"].set(str(ethics.get("decision_final") or "pendiente"))
            self.status_labels["docx_atlas_web"].set(
                str(state.get("docx_atlas_web", {}).get("estado") or "pendiente")
            )
            self.decision_var.set(str(ethics.get("decision_final") or "pausar") if ethics.get("decision_final") in backend.VALID_DECISIONS else "pausar")
            docx = self.docx_path()
            self.docx_path_var.set(f"DOCX: {backend.display_path(docx)}" if docx.exists() else "DOCX pendiente")
            can_build = (
                consent == "otorgado"
                and backend.anonymized_transcript_path(target).exists()
                and ethics.get("decision_final") == "exportable"
            )
            self.build_docx_button.state(["!disabled"] if can_build else ["disabled"])
            if not silent:
                self.log("Estado actualizado.")
        except Exception as exc:
            if not silent:
                self.show_error(exc)

    def create_or_verify_case(self) -> None:
        try:
            target = self.case_path()
            udan_id = self.id_var.get().strip() or backend.DEFAULT_UDAN_ID
            submission_id = self.submission_var.get().strip()
            if not target.exists():
                if not submission_id:
                    raise backend.UdanError("Registra un submission_id antes de crear el caso.")
                args = argparse.Namespace(
                    root=self.root_var.get(),
                    id=udan_id,
                    submission_id=submission_id,
                    comunidad="pendiente",
                    perfil_participante="pendiente",
                    tipo_relato="pendiente",
                    duracion="pendiente",
                    consentimiento="pendiente",
                    dry_run=False,
                )
                self.run_backend(backend.command_init_case, args)
                self.log("Caso piloto creado.")
            else:
                backend.append_log(target, "GUI verifico caso piloto.")
                self.log("Caso piloto verificado.")
            self.refresh_status(silent=True)
        except Exception as exc:
            self.show_error(exc)

    def register_consent(self) -> None:
        try:
            args = argparse.Namespace(
                root=self.root_var.get(),
                id=self.id_var.get(),
                consentimiento=self.consent_var.get(),
                notes="Registrado desde GUI local Corpus B.",
                dry_run=False,
            )
            self.run_backend(backend.command_set_consent, args)
            self.log(f"Consentimiento registrado: {self.consent_var.get()}.")
            self.refresh_status(silent=True)
            if self.consent_var.get() != "otorgado":
                messagebox.showwarning(
                    "Consentimiento",
                    "El flujo queda bloqueado para DOCX hasta que el consentimiento sea otorgado.",
                )
        except Exception as exc:
            self.show_error(exc)

    def confirm_overwrite(self, destination: Path) -> bool:
        if not destination.exists():
            return False
        return messagebox.askyesno(
            "Confirmar sobrescritura",
            f"Ya existe {backend.display_path(destination)}.\n\nDeseas sobrescribirlo?",
        )

    def select_audio(self) -> None:
        path = filedialog.askopenfilename(title="Seleccionar audio local autorizado", filetypes=AUDIO_TYPES)
        if not path:
            return
        try:
            source = Path(path)
            destination = self.case_path() / "01_audio_original_restringido" / source.name
            overwrite = self.confirm_overwrite(destination)
            if destination.exists() and not overwrite:
                self.log("Audio no registrado para evitar sobrescritura.")
                return
            args = argparse.Namespace(
                root=self.root_var.get(),
                id=self.id_var.get(),
                audio_path=path,
                dry_run=False,
                overwrite=overwrite,
            )
            self.run_backend(backend.command_attach_audio, args)
            self.log("Audio local registrado en expediente.")
            self.refresh_status(silent=True)
        except Exception as exc:
            self.show_error(exc)

    def select_transcript(self, title: str, command: Callable[[Any], int], destination: Path) -> None:
        path = filedialog.askopenfilename(title=title, filetypes=TXT_TYPES)
        if not path:
            return
        try:
            if Path(path).suffix.lower() != ".txt":
                raise backend.UdanError("Solo se aceptan archivos .txt.")
            overwrite = self.confirm_overwrite(destination)
            if destination.exists() and not overwrite:
                self.log("Transcripcion no registrada para evitar sobrescritura.")
                return
            args = argparse.Namespace(
                root=self.root_var.get(),
                id=self.id_var.get(),
                transcript_path=path,
                dry_run=False,
                overwrite=overwrite,
            )
            self.run_backend(command, args)
            self.log("Transcripcion registrada sin mostrar contenido.")
            self.refresh_status(silent=True)
        except Exception as exc:
            self.show_error(exc)

    def select_preliminary(self) -> None:
        destination = self.case_path() / "03_transcripcion_preliminar" / "TRANSCRIPCION_PRELIMINAR.txt"
        self.select_transcript("Seleccionar transcripcion preliminar", backend.command_attach_preliminary, destination)

    def select_reviewed(self) -> None:
        destination = self.case_path() / "04_transcripcion_revisada" / "TRANSCRIPCION_REVISADA.txt"
        self.select_transcript("Seleccionar transcripcion revisada", backend.command_attach_reviewed, destination)

    def select_anonymized(self) -> None:
        destination = self.case_path() / "05_transcripcion_anonimizada" / "TRANSCRIPCION_ANONIMIZADA_VERIFICADA.txt"
        self.select_transcript("Seleccionar transcripcion anonimizada", backend.command_attach_anonymized, destination)

    def register_ethics(self) -> None:
        try:
            target = self.case_path()
            metadata, state, _ethics = backend.read_case_files(target)
            if self.decision_var.get() == "exportable":
                if not backend.consent_is_granted(metadata, state):
                    raise backend.UdanError("No se permite exportable sin consentimiento otorgado.")
                if not backend.anonymized_transcript_path(target).exists():
                    raise backend.UdanError("No se permite exportable sin transcripcion anonimizada.")
            args = argparse.Namespace(
                root=self.root_var.get(),
                id=self.id_var.get(),
                decision=self.decision_var.get(),
                reviewed_by=self.reviewed_by_var.get().strip() or "investigador_principal",
                notes=self.notes_var.get().strip(),
                dry_run=False,
            )
            self.run_backend(backend.command_ethics_review, args)
            self.log(f"Revision etica registrada: {self.decision_var.get()}.")
            self.refresh_status(silent=True)
        except Exception as exc:
            self.show_error(exc)

    def build_docx(self) -> None:
        try:
            docx = self.docx_path()
            overwrite = self.confirm_overwrite(docx)
            if docx.exists() and not overwrite:
                self.log("DOCX no generado para evitar sobrescritura.")
                return
            args = argparse.Namespace(
                root=self.root_var.get(),
                id=self.id_var.get(),
                dry_run=False,
                overwrite=overwrite,
            )
            self.run_backend(backend.command_build_docx, args)
            self.log("DOCX ATLAS.ti Web generado.")
            self.refresh_status(silent=True)
            messagebox.showinfo("DOCX generado", backend.display_path(docx))
        except Exception as exc:
            self.show_error(exc)

    def validate_case(self) -> None:
        try:
            result = self.run_backend(
                backend.command_validate,
                argparse.Namespace(root=self.root_var.get(), id=self.id_var.get()),
            )
            self.refresh_status(silent=True)
            if result == 0:
                messagebox.showinfo("Validacion", "Caso valido.")
                self.log("Validacion completada sin errores.")
            else:
                messagebox.showwarning("Validacion", "La validacion encontro pendientes o errores.")
                self.log("Validacion encontro pendientes o errores.")
        except Exception as exc:
            self.show_error(exc)

    def open_folder(self, path: Path) -> None:
        try:
            if not path.exists():
                raise backend.UdanError(f"No existe la carpeta: {backend.display_path(path)}")
            if sys.platform.startswith("win"):
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                messagebox.showinfo("Ruta", str(path))
            self.log(f"Carpeta abierta: {backend.display_path(path)}")
        except Exception as exc:
            self.show_error(exc)

    def open_case_folder(self) -> None:
        self.open_folder(self.case_path())

    def open_docx_folder(self) -> None:
        self.open_folder(self.case_path() / "06_uda_docx_atlas_web")


def main() -> int:
    app = CorpusBGui()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
