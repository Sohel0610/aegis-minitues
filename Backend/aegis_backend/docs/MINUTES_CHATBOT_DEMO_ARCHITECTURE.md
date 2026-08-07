# Minutes Chatbot: Demo Architecture

## Request path

`Azure AD SSO -> signed Aegis session -> FastAPI -> query router -> retrieval/tools -> GPT-4.1 mini -> cited answer`

The API derives the user from the signed session, then scopes every document and structured-data query to that user. Administrators retain their explicitly granted cross-user access.

## Retrieval choices

| Question type | Path | Why |
| --- | --- | --- |
| Exact names, figures, IDs, dates | Lexical BM25 + dense vector search | Exact terms and semantic paraphrases both matter. |
| Normal document Q&A | Hybrid RAG with reciprocal-rank fusion | Robust ranking without needing score calibration. |
| Comparison, risk, conflict, trend | Agentic RAG synthesis | Retrieves evidence across sources, then asks the model to compare only that evidence. |
| Agenda, decision, action-item query | Read-only structured tools plus RAG | Database records are authoritative; documents supply detail. |

## Document ingestion

The local demo pipeline preserves PDF page, PPT slide, and XLSX sheet boundaries, extracts DOCX tables, chunks the extracted content, and creates embeddings. Scanned or layout-heavy PDFs must be sent to Azure Document Intelligence before indexing; local PDF text extraction is not an OCR solution.

## Production next steps

1. Move vectors and keyword index to Azure AI Search (hybrid query, semantic ranker, filters on tenant/user/document).
2. Use Azure Blob Storage for originals and an asynchronous ingestion queue for extraction/indexing.
3. Add Azure Document Intelligence `prebuilt-layout` for scanned PDFs, tables, and complex layouts.
4. Add audit events, evaluation dataset, retrieval quality metrics, prompt-injection checks, and document-level retention/deletion.
5. Add email as a separate approval-gated tool: generate preview -> confirm recipient/content -> send through approved Azure Communication Services/Graph integration -> audit log.
