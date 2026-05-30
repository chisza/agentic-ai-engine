"""Upload sample corpus documents to GCS and import them into the Vertex AI RAG corpus.

Usage:
    python scripts/upload_rag_corpus.py

Requires:
    - GOOGLE_CLOUD_PROJECT env var (or defaults from app/config.py)
    - GOOGLE_CLOUD_STORAGE_BUCKET env var (or default "agentic-ai-eng-bucket")
    - Authenticated gcloud credentials with Storage and Vertex AI permissions
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Allow importing from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.cloud import storage

from app import config
from app.context.rag.rag_engine_handler import rag_engine_handler

ROOT = Path(__file__).parent.parent

CORPUS_SOURCES = [
    (ROOT / "app" / "agent_repo" / "summarizer_agent" / "corpus", "rag-corpus/summarizer"),
    (ROOT / "app" / "agent_repo" / "pdf_converter_team" / "corpus", "rag-corpus/pdf-converter"),
]


def upload_to_gcs(bucket_name: str) -> list[str]:
    """Upload all markdown files from all corpus directories to GCS.

    Returns a list of gs:// URIs for the uploaded files.
    """
    client = storage.Client(project=config.GOOGLE_CLOUD_PROJECT)
    bucket = client.bucket(bucket_name)
    uris = []

    for corpus_dir, gcs_prefix in CORPUS_SOURCES:
        if not corpus_dir.exists():
            print(f"  Skipping {corpus_dir} (not found)")
            continue
        for md_file in sorted(corpus_dir.glob("*.md")):
            blob_name = f"{gcs_prefix}/{md_file.name}"
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(str(md_file), content_type="text/markdown")
            uri = f"gs://{bucket_name}/{blob_name}"
            print(f"  Uploaded {md_file.name} → {uri}")
            uris.append(uri)

    return uris


async def main() -> None:
    bucket = config.GOOGLE_CLOUD_STORAGE_BUCKET
    print(f"Uploading corpus documents to gs://{bucket}/")
    uris = upload_to_gcs(bucket)
    if not uris:
        print("No .md files found in any corpus directory.")
        return

    print(f"\nImporting {len(uris)} file(s) into Vertex AI RAG corpus...")
    if not rag_engine_handler.available:
        print("ERROR: RAG corpus is not available. Check your GCP credentials and region.")
        sys.exit(1)

    result = await rag_engine_handler.import_files(uris)
    if result.get("status") == "ok":
        print(f"Done. Imported {result['imported_count']} file(s) into corpus: {rag_engine_handler.corpus_name}")
    else:
        print(f"Import failed: {result.get('message')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
