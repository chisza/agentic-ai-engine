"""RAG-based tools for the PDF converter team.

lookup_definitions  – semantic search against the corpus for term definitions.
add_to_knowledge_base – uploads a converted document to GCS and imports it
                        into the Vertex AI RAG corpus so future lookups can
                        draw on its content.

All Vertex AI and GCS calls run in a thread pool so the event loop is never
blocked.
"""

from __future__ import annotations

import asyncio
import re

import structlog

from app import config
from app.context.rag.rag_engine_handler import rag_engine_handler

logger = structlog.get_logger(__name__)

_CORPUS_TIMEOUT = 15.0   # seconds to wait for lazy corpus init
_QUERY_TIMEOUT  = 30.0   # seconds for retrieval query


async def lookup_definitions(terms: str) -> str:
    """Search the knowledge base for definitions of technical terms.

    Use this ONLY when the user explicitly asks to add definitions, annotate
    terms, or enrich the document with explanations.  Pass the key technical
    terms found in the extracted text as a comma-separated list or a short
    descriptive phrase.

    Args:
        terms: Comma-separated technical terms or a phrase describing what
               to look up (e.g. "TCP/IP, REST API, microservices").
    """
    try:
        corpus = await asyncio.wait_for(
            asyncio.to_thread(lambda: rag_engine_handler.corpus_name),
            timeout=_CORPUS_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.warning("RAG corpus init timed out")
        return "Definition lookup is not available right now (corpus initialisation timed out)."

    if not corpus:
        return "Definition lookup is not available (no RAG corpus configured)."

    def _query() -> list[str]:
        import vertexai
        from vertexai.preview import rag

        vertexai.init(
            project=config.GOOGLE_CLOUD_PROJECT,
            location=config.GOOGLE_CLOUD_LOCATION,
        )
        response = rag.retrieval_query(
            text=terms,
            rag_corpora=[corpus],
            similarity_top_k=5,
            vector_distance_threshold=0.5,
        )
        if not response.contexts.contexts:
            return []
        return [ctx.text for ctx in response.contexts.contexts]

    try:
        results = await asyncio.wait_for(
            asyncio.to_thread(_query),
            timeout=_QUERY_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.warning("RAG retrieval timed out", terms=terms)
        return "Definition lookup timed out."
    except Exception as e:
        logger.error("RAG retrieval failed", terms=terms, error=str(e))
        return f"Definition lookup failed: {e}"

    if not results:
        return f"No definitions found in the knowledge base for: {terms}"

    return "\n\n---\n\n".join(results)


async def add_to_knowledge_base(title: str, content: str) -> str:
    """Upload a converted document to GCS and import it into the RAG corpus.

    Use this ONLY when the user explicitly asks to save the document to the
    knowledge base so future definition lookups can draw on its content.

    Args:
        title: A short descriptive title for the document (used as the filename).
        content: The full Markdown text of the converted document.
    """
    def _upload_and_import() -> str:
        from google.cloud import storage

        # Sanitise title for use as a GCS blob name
        safe = re.sub(r"[^a-zA-Z0-9_-]", "_", title)[:60] or "document"
        blob_name = f"rag-corpus/pdf-converter/uploaded/{safe}.md"
        bucket_name = config.GOOGLE_CLOUD_STORAGE_BUCKET

        client = storage.Client(project=config.GOOGLE_CLOUD_PROJECT)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_string(content.encode("utf-8"), content_type="text/markdown")
        logger.info("Uploaded document to GCS", blob=blob_name)
        return f"gs://{bucket_name}/{blob_name}"

    try:
        gcs_uri = await asyncio.wait_for(
            asyncio.to_thread(_upload_and_import),
            timeout=60.0,
        )
    except asyncio.TimeoutError:
        return "Upload timed out. Please try again."
    except Exception as e:
        logger.error("GCS upload failed", title=title, error=str(e))
        return f"Upload failed: {e}"

    # Import the uploaded file into the RAG corpus
    try:
        corpus = await asyncio.wait_for(
            asyncio.to_thread(lambda: rag_engine_handler.corpus_name),
            timeout=_CORPUS_TIMEOUT,
        )
    except asyncio.TimeoutError:
        return f"Uploaded to GCS ({gcs_uri}) but RAG import timed out."

    if not corpus:
        return f"Uploaded to GCS ({gcs_uri}) but no RAG corpus is configured."

    result = await rag_engine_handler.import_files([gcs_uri])
    if result.get("status") == "ok":
        logger.info("Document imported into RAG corpus", title=title, gcs_uri=gcs_uri)
        return (
            f"Document '{title}' has been added to the knowledge base "
            f"({result.get('imported_count', 1)} file imported). "
            f"Future definition lookups will include its content."
        )
    return f"Uploaded to GCS but RAG import failed: {result.get('message')}"
