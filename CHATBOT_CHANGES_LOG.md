# Minutes Chatbot Changes Log

**Status:** Local workspace changes only. Nothing has been deployed to the Azure VM, merged, or connected to email delivery.

## Files changed

| File | Functions / areas changed | Why |
| --- | --- | --- |
| `Backend/aegis_backend/chatbot_minutes/services/retrieval_service.py` | **New file.** `HybridRetrievalService.route_query`, `retrieve`, `run_structured_tools` | Adds hybrid retrieval: semantic vector similarity plus lexical BM25 ranking, combined with reciprocal-rank fusion. It also routes comparison/risk questions to a grounded “agentic RAG” synthesis path and exposes read-only tools for action items, decisions, and agendas. |
| `Backend/aegis_backend/chatbot_minutes/services/document_extractor.py` | **New file.** `extract_text` | Replaces placeholder ingestion with extractors that retain document structure: PDF page labels, Word tables, PowerPoint slide labels, and Excel sheet labels. This makes citations and financial-data questions more useful. It does **not** provide OCR for scanned PDFs. |
| `Backend/aegis_backend/chatbot_minutes/services/chatbot_service.py` | `__init__`, `process_query`, `_build_context`, `_generate_answer` | Uses the new hybrid retrieval service, adds read-only structured tool results to context, returns the retrieval mode to the UI, and changes the prompt so answers are grounded in supplied evidence rather than invented from model knowledge. |
| `Backend/aegis_backend/chatbot_minutes/router.py` | `get_current_chatbot_user`, `QueryResponse`, `process_query`, `upload_document` | Uses signed session identity instead of a browser-provided email header; adds retrieval mode to responses; validates upload size; invokes the new extractor; rejects files with no readable text instead of silently indexing placeholder content. |
| `Backend/aegis_backend/chatbot_minutes/config.py` | `MAX_FILE_SIZE` | Makes the maximum upload size configurable with `CHATBOT_MAX_FILE_SIZE`; default changed from 10 MB to 50 MB for demo documents. |
| `Backend/aegis_backend/routes/auth.py` | `azure_ad_callback` | Issues the existing signed Aegis session token after Azure AD login. This is required because the chatbot now verifies the identity in the `Authorization` header. |
| `Frontend/src/pages/minutes-preparation/MinutesChatbot.tsx` | `authHeaders`, session/history/query/upload requests, message metadata, empty-state text | Sends the signed bearer token to the chatbot API, shows the retrieval mode under answers, and updates sample prompts/text to reflect PPT, Excel, comparisons, and citations. |
| `Backend/aegis_backend/docs/MINUTES_CHATBOT_DEMO_ARCHITECTURE.md` | **New file.** | Documents the request path, when each RAG mode is used, local ingestion limitations, and the recommended Azure production architecture. |

## Why hybrid RAG was added

Dense vector search is useful when a question paraphrases document text. It can be weak for exact financial values, dates, company names, identifiers, and table headings. Lexical BM25 retrieval is strong for those exact terms. Combining both gives better demo behaviour than vector-only retrieval.

## When each mode is used

| User question pattern | Mode | Behaviour |
| --- | --- | --- |
| Ordinary document question | `hybrid_rag` | Retrieves source chunks using vector and keyword ranking. |
| “Compare”, “risk”, “trend”, “conflict”, “impact”, or cross-document question | `agentic_rag` | Retrieves broader evidence first; the model synthesizes and identifies differences/inferences from that evidence only. |
| “Action item”, “decision”, “agenda”, or meeting query | `structured_plus_rag` | Reads matching structured database records and combines them with relevant document evidence. |

## Important limitations and next actions

1. **Azure Document Intelligence is still needed** for scanned PDFs, complex layouts, tables, handwriting, and high-quality OCR. The local extractor only handles machine-readable text.
2. The current hybrid retrieval reads the existing JSON embeddings from PostgreSQL. For production scale, move retrieval to **Azure AI Search** with user/document filters and hybrid + semantic ranking.
3. Email sending was deliberately not implemented in this change. It should be an approval-gated tool: preview -> user confirms recipient/content -> Azure Communication Services or Microsoft Graph sends -> audit log.
4. The new signed-session flow requires `AEGIS_SESSION_SECRET` to be set securely on the Azure VM before production deployment.
5. No database schema migration was required by these changes.

## Management justification: Azure AI Document Intelligence

Azure AI Document Intelligence is required to make the chatbot dependable for the complex business documents expected in this project. The current local extraction is suitable only for documents that already contain clean, machine-readable text; it is not a production OCR or layout-understanding service.

### Business problem it solves

| Document situation | Limitation without Document Intelligence | Benefit with Azure AI Document Intelligence |
| --- | --- | --- |
| Scanned PDFs and image-only documents | Text may be empty, garbled, or unavailable. The chatbot cannot safely answer from it. | OCR extracts readable text with page-level evidence. |
| Financial statements and Excel-like tables embedded in PDFs | Rows, columns, headings, and values can be extracted in the wrong order, causing incorrect financial interpretation. | Layout/table extraction preserves table structure and relationships between headers and values. |
| Complex board packs, presentations, and multi-column reports | Reading order is often incorrect; footnotes, captions, and section boundaries are lost. | Layout analysis identifies pages, paragraphs, tables, headings, and reading order. |
| Forms, invoices, and standard corporate templates | Important fields must be found consistently across many files. | Prebuilt models and optional custom extraction models return named fields in structured JSON. |
| Audit/review questions | A response needs traceability back to the original source. | Page, paragraph, table, and bounding-region references can be stored with chatbot citations. |

### Why local OCR/Tesseract alone is not enough

1. Tesseract performs optical character recognition only. It does not reliably reconstruct complex table relationships, multi-column reading order, charts, form fields, or page layout.
2. Financial and governance documents require high precision. A transposed digit, detached table header, or wrong reading order can create a misleading answer and an audit risk.
3. A local OCR pipeline would require separate work for scaling, language packs, quality monitoring, retries, document classification, table parsing, security hardening, and maintenance. That is substantial engineering work outside the chatbot feature itself.
4. Document Intelligence provides a managed Azure service designed for OCR and layout extraction, which is a better fit for the existing Azure-hosted architecture.

### Proposed controlled implementation

1. Start with the `prebuilt-layout` model for scanned PDFs, board packs, tables, and complex reports.
2. Keep the original file in Azure Blob Storage; store extracted text, tables, page number, and source coordinates as searchable metadata.
3. Route documents automatically: use local extraction for simple native-text files, and Document Intelligence for scanned/complex PDFs or whenever local extraction produces low-quality text.
4. Run a pilot on a representative, approved set of financial reports, PPTs, board minutes, and scanned documents. Measure extraction accuracy, table accuracy, processing time, and estimated cost per page before a full rollout.
5. Keep human review for high-impact outputs such as financial numbers, regulatory statements, and board decisions.

### Security and governance points

- Use the organisation's Azure subscription, region, private networking/private endpoint where required, managed identity, and Azure Key Vault for credentials.
- Restrict access through existing SSO/RBAC; the chatbot must only retrieve documents the signed-in user is allowed to access.
- Maintain an audit record of upload, extraction, retrieval sources, user, timestamp, and any later email/export action.
- Apply retention/deletion rules to both Blob originals and extracted/indexed content.
- Confirm the Azure region, data-residency policy, and approved document classification with Information Security before production use.

### Approval requested from management

Approval is requested for a limited Azure AI Document Intelligence pilot using `prebuilt-layout`, Azure Blob Storage, and Azure AI Search integration. The goal is to validate accurate extraction of complex financial and governance documents before the user demo and production rollout.

## Validation performed

- Python syntax compilation passed for the modified chatbot and authentication backend modules.
- Frontend build was not run in the first attempt because the command used an incorrect directory. npm is available at `/usr/local/bin/npm`; run `npm run build` from `Frontend/` before deployment.

## Advanced implementation update

The advanced implementation and Azure VM target configuration are documented in [Backend/aegis_backend/docs/ADVANCED_CHATBOT_IMPLEMENTATION.md](Backend/aegis_backend/docs/ADVANCED_CHATBOT_IMPLEMENTATION.md). It includes the complete function/feature matrix, Tesseract behaviour, reference-PDF assessment, Azure VM service design, Azure AI Search index contract, Cohere/LLM configuration, and the approval-gated email workflow.

## Azure configuration update

Switched the backend to a single shared `.env` source of truth via [Backend/aegis_backend/utils/shared_env.py](Backend/aegis_backend/utils/shared_env.py), plus Azure AI Search index provisioning and upload synchronisation. Credentials shared in conversation were intentionally not copied into repository files; rotate them and place their replacements in the backend `.env` or VM secret storage. The supplied Blob detail was an Azure AI Search URL, so a real Blob Storage endpoint/container is still required before Blob uploads can be enabled.
