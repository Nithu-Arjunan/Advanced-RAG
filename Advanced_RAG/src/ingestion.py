import logging
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Literal

from pypdf import PdfReader


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOADED_DOCS_FILE = DATA_DIR / "uploaded_documents.json"
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}

# Simple in-memory trackers.
UPLOADED_DOCUMENTS: list[dict[str, str]] = []
INGESTED_DOCUMENTS: set[tuple[str, str]] = set()

logging.basicConfig(level=logging.INFO)

def ensure_data_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_path(path: str) -> str:
    return os.path.normcase(os.path.abspath(path))


def _load_uploaded_documents() -> list[dict[str, str]]:
    ensure_data_dirs()
    if not UPLOADED_DOCS_FILE.exists():
        return []
    try:
        raw = json.loads(UPLOADED_DOCS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(raw, list):
        return []

    docs: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        docs.append(
            {
                "file_name": str(item.get("file_name", "")),
                "file_path": str(item.get("file_path", "")),
                "namespace": str(item.get("namespace", "")),
                "uploaded_at": str(item.get("uploaded_at", "")),
            }
        )
    return docs


def _save_uploaded_documents(documents: list[dict[str, str]]) -> None:
    ensure_data_dirs()
    UPLOADED_DOCS_FILE.write_text(
        json.dumps(documents, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def add_uploaded_document(file_path: str, namespace: str = "") -> None:
    entry = {
        "file_name": os.path.basename(file_path),
        "file_path": file_path,
        "namespace": namespace,
        "uploaded_at": _utc_now_iso(),
    }
    documents = _load_uploaded_documents()
    documents.append(entry)
    _save_uploaded_documents(documents)
    UPLOADED_DOCUMENTS.append(entry)


def list_uploaded_documents() -> list[dict[str, str]]:
    ensure_data_dirs()
    documents = _load_uploaded_documents()
    seen_records = {
        (str(doc.get("file_path", "")), str(doc.get("uploaded_at", "")))
        for doc in documents
    }
    changed = False

    # Merge current-process entries that may not be flushed yet.
    for doc in UPLOADED_DOCUMENTS:
        key = (str(doc.get("file_path", "")), str(doc.get("uploaded_at", "")))
        if key in seen_records:
            continue
        documents.append(
            {
                "file_name": str(doc.get("file_name", "")),
                "file_path": str(doc.get("file_path", "")),
                "namespace": str(doc.get("namespace", "")),
                "uploaded_at": str(doc.get("uploaded_at", "")),
            }
        )
        seen_records.add(key)
        changed = True

    # Keep only records whose files still exist.
    existing_docs: list[dict[str, str]] = []
    tracked_paths = set()
    for doc in documents:
        file_path = str(doc.get("file_path", ""))
        if not file_path or not os.path.isfile(file_path):
            changed = True
            continue
        existing_docs.append(doc)
        tracked_paths.add(_normalize_path(file_path))
    documents = existing_docs

    # Backfill from files on disk so listing works across server restarts.
    for entry in UPLOAD_DIR.iterdir():
        if not entry.is_file():
            continue

        abs_path = _normalize_path(str(entry))
        if abs_path in tracked_paths:
            continue

        uploaded_at = datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc).isoformat()
        documents.append(
            {
                "file_name": entry.name,
                "file_path": str(entry),
                "namespace": "",
                "uploaded_at": uploaded_at,
            }
        )
        changed = True

    if changed:
        _save_uploaded_documents(documents)
    UPLOADED_DOCUMENTS[:] = documents
    return documents


def remove_uploaded_document(file_name: str) -> int:
    documents = list_uploaded_documents()
    kept: list[dict[str, str]] = []
    removed = 0
    for doc in documents:
        stored_name = str(doc.get("file_name", ""))
        file_path = str(doc.get("file_path", ""))
        if stored_name == file_name or os.path.basename(file_path) == file_name:
            removed += 1
            continue
        kept.append(doc)
    if removed:
        _save_uploaded_documents(kept)
        UPLOADED_DOCUMENTS[:] = kept
    return removed


def clear_uploaded_documents() -> None:
    _save_uploaded_documents([])
    UPLOADED_DOCUMENTS.clear()


def is_document_ingested(file_name: str, strategy: Literal["parent_child", "sentence_window"]) -> bool:
    return (file_name, strategy) in INGESTED_DOCUMENTS


def mark_document_ingested(file_name: str, strategy: Literal["parent_child", "sentence_window"]) -> None:
    INGESTED_DOCUMENTS.add((file_name, strategy))


def extract_text_from_pdf(file_path: str) -> List[Dict]:
    reader = PdfReader(file_path)

    pages = []
    file_name = os.path.basename(file_path)
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({"page": i + 1, "text": text, "source": file_name})

    logging.info(f"Extracted text from {len(pages)} pages in PDF: {file_path}")
    return pages


def extract_text_from_txt(file_path: str) -> List[Dict]:
    with open(file_path, "r", encoding="utf-8") as f:
        logging.info(f"Extracted text from TXT file: {file_path}")
        return [{"page": 1, "text": f.read(), "source": os.path.basename(file_path)}]


def extract_text(file_path: str) -> List[Dict]:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    if ext in (".txt", ".md"):
        return extract_text_from_txt(file_path)
    raise ValueError(f"Unsupported file type:{ext}")
