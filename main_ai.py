# main_ai.py — ORM Analyzer integrado con pipeline IA PRO
# Fecha: 2025-10-19
# Ejecuta limpieza, análisis y generación de informe completo.

import os
import sys
from pathlib import Path
try:
    from dotenv import load_dotenv, find_dotenv
except Exception:
    load_dotenv = None
    find_dotenv = None
import yaml
import re
import logging
import argparse
import hashlib
import json
from datetime import datetime, timezone

def _load_env_once() -> None:
    def _load_env_fallback(p: Path) -> None:
        try:
            text = p.read_text(encoding="utf-8-sig")
        except Exception:
            return
        for raw in text.splitlines():
            line = (raw or "").strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].lstrip()
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            key = (k or "").strip()
            if not key or key in os.environ:
                continue
            val = (v or "").strip().strip('"').strip("'")
            os.environ[key] = val

    here = Path(__file__).resolve().parent
    env1 = here / ".env"
    if env1.exists():
        if load_dotenv is not None:
            load_dotenv(dotenv_path=str(env1), override=False)
        else:
            _load_env_fallback(env1)
        return

    env2_path = None
    if find_dotenv is not None:
        env2 = find_dotenv(".env", usecwd=True)
        if env2:
            env2_path = Path(env2)
    else:
        env2_cwd = Path.cwd() / ".env"
        if env2_cwd.exists():
            env2_path = env2_cwd

    if env2_path is not None:
        if load_dotenv is not None:
            load_dotenv(dotenv_path=str(env2_path), override=False)
        else:
            _load_env_fallback(env2_path)


_load_env_once()

# Asegurar que src esté en el path de Python
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pandas as pd
from analyze_reviews import run_full_pipeline
from report_generator_ai_pro import create_report_ai_pro
from report_generator_modern import create_modern_report
from pdf_generator_modern import create_modern_pdf_report
from report_generator_professional import (
    create_professional_report,
    PIPELINE_VERSION,
    QualityCheckError,
    OutputContractError,
    _normalize_client_name,
    _safe_filename,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================
# CONFIGURACIÓN GLOBAL
# =============================================================

DEFAULT_CONFIG = {
    "openai_model": "gpt-4o-mini",
    "openai_temperature": 0.3,
    "enable_ai_owner": True,
    "enable_ai_analysis": True,
    "enable_sector_context": False,
    "output_dir": BASE_DIR / "data" / "reports",
    "report_title": "Informe ORM y CX",
    "use_professional_format": True,
    "fake_review_threshold": 0.5,
}


def load_config():
    config_path = BASE_DIR / "config.yaml"
    cfg = DEFAULT_CONFIG.copy()

    if config_path.exists():
        try:
            with config_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            data = {}

        openai_cfg = data.get("openai", {})
        report_cfg = data.get("report", {})
        paths_cfg = data.get("paths", {})
        analysis_cfg = data.get("analysis", {})
        metrics_cfg = data.get("metrics", {})

        if "model" in openai_cfg:
            cfg["openai_model"] = openai_cfg["model"]
        if "temperature" in openai_cfg:
            cfg["openai_temperature"] = openai_cfg["temperature"]
        if "title" in report_cfg:
            cfg["report_title"] = report_cfg["title"]
        if "use_professional_format" in report_cfg:
            cfg["use_professional_format"] = bool(report_cfg["use_professional_format"])
        if "enable_ai_owner" in report_cfg:
            cfg["enable_ai_owner"] = bool(report_cfg["enable_ai_owner"])
        if "enable_ai_analysis" in report_cfg:
            cfg["enable_ai_analysis"] = bool(report_cfg["enable_ai_analysis"])
        if "enable_sector_context" in report_cfg:
            cfg["enable_sector_context"] = bool(report_cfg["enable_sector_context"])
        if "output_mode" in report_cfg:
            raw_mode = str(report_cfg.get("output_mode", "CLIENT")).upper()
            if raw_mode not in ("CLIENT", "AUDIT"):
                raw_mode = "CLIENT"
            cfg["output_mode"] = raw_mode
            cfg["report_mode"] = raw_mode
        if "output_dir" in paths_cfg:
            cfg["output_dir"] = BASE_DIR / paths_cfg["output_dir"]
        if "fake_review_threshold" in analysis_cfg:
            cfg["fake_review_threshold"] = analysis_cfg["fake_review_threshold"]
        if "version" in metrics_cfg:
            raw_metrics_version = str(metrics_cfg.get("version", "v1"))
            if not re.match(r"^v[0-9]+$", raw_metrics_version):
                raw_metrics_version = "v1"
            cfg["metrics_version"] = raw_metrics_version

    if "metrics_version" not in cfg:
        cfg["metrics_version"] = "v1"

    if "output_mode" not in cfg:
        cfg["output_mode"] = "CLIENT"
    if "report_mode" not in cfg:
        cfg["report_mode"] = cfg["output_mode"]

    return cfg


CONFIG = load_config()


# =============================================================
# FUNCIÓN PRINCIPAL
# =============================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dev", "prod"], default="dev")
    parser.add_argument("--input", dest="input_path", default=None)
    args = parser.parse_args()

    mode = str(args.mode or "dev").strip().lower()
    started_at = datetime.now(timezone.utc).isoformat()

    print("=== ORM Analyzer IA PRO ===\n")
    logger.info(f"PIPELINE_VERSION={PIPELINE_VERSION} mode={mode}")

    if mode == "prod" and not os.getenv("OPENAI_API_KEY"):
        print(
            "❌ Falta OPENAI_API_KEY. Defínela en un archivo .env o como variable de entorno "
            "en tu shell/CI y vuelve a ejecutar."
        )
        print("Ejemplo (.env): OPENAI_API_KEY=tu_clave_aqui")
        return 13

    # --- Solicitar JSON al usuario ---
    if mode == "prod":
        if not args.input_path:
            print("❌ En modo prod debes pasar --input con la ruta al JSON.")
            return 12
        csv_path = Path(str(args.input_path).strip().strip('"'))
    else:
        if args.input_path:
            csv_path = Path(str(args.input_path).strip().strip('"'))
        else:
            csv_path = Path(input("Ruta completa del JSON del cliente: ").strip().strip('"'))

    if not csv_path.exists():
        print(f"❌ No se encontró el archivo: {csv_path}")
        return 12 if mode == "prod" else 1

    print(f"\n📂 Analizando: {csv_path.name}\n")

    # --- Pipeline completo (limpieza + análisis) ---
    results = run_full_pipeline(
        csv_path, fake_threshold=CONFIG.get("fake_review_threshold", 0.5)
    )
    df_clean = results["dataframe"]
    if "place_metadata" in results and "place_metadata" not in CONFIG:
        CONFIG["place_metadata"] = results["place_metadata"]
    if "languages" in results and "languages" not in CONFIG:
        CONFIG["languages"] = results["languages"]
    if "engagement" in results and "engagement" not in CONFIG:
        CONFIG["engagement"] = results["engagement"]

    # --- Preparar variables para el informe ---
    client_name = csv_path.stem
    CONFIG["source_csv"] = str(csv_path)
    CONFIG["mode"] = mode
    if mode == "prod":
        CONFIG["require_pdf"] = True

    def _sha256_file_main(path: Path) -> str | None:
        try:
            h = hashlib.sha256()
            with path.open("rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return None

    input_hash = _sha256_file_main(csv_path)

    client_clean = _normalize_client_name(client_name)
    safe_name = _safe_filename(client_clean)
    expected_out_dir = Path(CONFIG.get("output_dir", BASE_DIR / "data" / "reports")) / safe_name / f"v{PIPELINE_VERSION}"

    # --- Generar informe ---
    print("\n🧠 Generando informe con IA...")
    
    exit_code = 0
    status = "OK"
    report_path = None
    try:
        if CONFIG.get("use_professional_format", False):
            print("📊 Usando formato profesional con tablas estilo consultoría...")
            report_path = create_professional_report(
                df_clean,
                client_name=client_name,
                output_path=CONFIG["output_dir"],
                cfg=CONFIG,
                project_root=PROJECT_ROOT,
            )
            print(f"\n✅ Informe profesional generado:")
            print(f"📄 Archivo: {report_path}")
            print("📋 Incluye tablas profesionales, análisis visual y recomendaciones estratégicas")
        else:
            output_path = create_report_ai_pro(
                df_clean,
                client_name=client_name,
                output_path=CONFIG["output_dir"],
                cfg=CONFIG,
                project_root=PROJECT_ROOT,
            )
            print(f"\n✅ Informe clásico generado en:\n{output_path}\n")
    except QualityCheckError as e:
        print(str(e))
        exit_code = 10 if mode == "prod" else 1
        status = "FAILED"
    except OutputContractError as e:
        print(f"❌ {e}")
        exit_code = 11 if mode == "prod" else 1
        status = "FAILED"
    except Exception as e:
        print(f"❌ Error no controlado: {e}")
        exit_code = 12 if mode == "prod" else 1
        status = "FAILED"
    finally:
        finished_at = datetime.now(timezone.utc).isoformat()
        if mode == "prod" or expected_out_dir.exists():
            try:
                expected_out_dir.mkdir(parents=True, exist_ok=True)

                docx_candidates = sorted(expected_out_dir.glob("*_informe_PROFESIONAL.docx"))
                pdf_candidates = sorted(expected_out_dir.glob("*_informe_PROFESIONAL.pdf"))
                docx_real = docx_candidates[0] if len(docx_candidates) == 1 else None
                pdf_real = pdf_candidates[0] if len(pdf_candidates) == 1 else None

                docx_hash = _sha256_file_main(docx_real) if docx_real else None
                pdf_hash = _sha256_file_main(pdf_real) if pdf_real else None

                log_path = expected_out_dir / "execution_log.json"
                base_payload = {}
                if log_path.exists():
                    try:
                        base_payload = json.loads(log_path.read_text(encoding="utf-8-sig") or "{}")
                    except Exception:
                        base_payload = {}
                if not isinstance(base_payload, dict):
                    base_payload = {}

                base_payload.update(
                    {
                        "pipeline_version": PIPELINE_VERSION,
                        "mode": mode,
                        "input_hash": input_hash,
                        "docx_hash": docx_hash,
                        "pdf_hash": pdf_hash,
                        "started_at": started_at,
                        "finished_at": finished_at,
                        "status": status,
                        "exit_code": exit_code,
                    }
                )
                if docx_real:
                    base_payload["file_generated"] = str(docx_real)
                if pdf_real:
                    base_payload["pdf_generated"] = str(pdf_real)

                log_path.write_text(json.dumps(base_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass

    if exit_code != 0:
        return exit_code

    else:
        return 0


# =============================================================
# EJECUCIÓN DIRECTA
# =============================================================

if __name__ == "__main__":
    raise SystemExit(main())
