# Minutes Chatbot — Development Handoff

## Status

The advanced Minutes Chatbot is implemented for the local demo and has a production configuration path for Azure. It has **not** been deployed to Azure and no supplied credential has been written to source control or used by the application during this work.

The shared Azure and PostgreSQL secrets must be rotated before any production deployment. Put replacement values only in the Azure VM's protected `.env` file, Key Vault, or managed identity configuration.

## What the chatbot now does

- Uploads and processes PDF, DOCX, PPTX, XLSX, CSV, TXT, and supported image files.
- Extracts native PDF text first; uses local Tesseract only when pages have insufficient native text.
- Preserves page, slide, and sheet locations in chunk metadata.
- Uses hybrid retrieval: semantic vector similarity plus BM25 keyword relevance.
- Supports a vectorless structured retrieval path for numeric, tabular, and metadata queries.
- Plans each query before retrieval: document question, summary, comparison, extraction, timeline, or out-of-scope conversation.
- Adds document-scoped retrieval, short-term chat memory, saved session summaries, entity memory, grounding checks, confidence labels, and conflict warnings.
- Shows sources as clickable evidence chips instead of leaking `[Source …]` strings into the answer.
- Provides safe Markdown rendering, upload/processing status, selected-document scope, and a responsive document-library UI.
- Uses a provider-neutral LLM layer: Groq for local demo; Azure AI Foundry Llama Maverick or Azure OpenAI GPT-4.1 mini for production/fallback.
- Supports local SentenceTransformers and a planned Azure Cohere embedding configuration.
- Supports PostgreSQL/pgvector locally through the same application model and an Azure AI Search indexing/retrieval route for production scale.

## Files changed for this chatbot work

| File | Why it changed |
|---|---|
| `Backend/aegis_backend/chatbot_minutes/config.py` | Centralised local versus Azure settings; LLM, embedding, retrieval, database, search, and OCR provider selection. |
| `Backend/aegis_backend/chatbot_minutes/database.py` | Added safe local SQLite support and non-destructive schema upgrades. |
| `Backend/aegis_backend/chatbot_minutes/models.py` | Added document processing metadata, chunk metadata, response metadata, session summaries, user preferences, and conversation entities. |
| `Backend/aegis_backend/chatbot_minutes/router.py` | Added secure upload/query endpoints, document selection, status endpoint, extraction/indexing flow, and local SSO-safe behaviour. |
| `Backend/aegis_backend/chatbot_minutes/services/chatbot_service.py` | Orchestrates planning, retrieval, tools, answer grounding, memory, and response metadata. |
| `Backend/aegis_backend/chatbot_minutes/services/embedding_service.py` | Added cached local SentenceTransformer embeddings, source-aware chunking, and Cohere Azure configuration support. |
| `Backend/aegis_backend/chatbot_minutes/services/retrieval_service.py` | Added local hybrid (vector + BM25) search, structured/vectorless tools, relevance filtering, sibling context, and Azure AI Search query support. |
| `Backend/aegis_backend/chatbot_minutes/services/document_extractor.py` | Added native extraction for complex PDFs, Word, PowerPoint, spreadsheets, images, Tesseract fallback, and optional Azure Document Intelligence. |
| `Backend/aegis_backend/chatbot_minutes/services/chat_history_service.py` | Added persistent conversation history, summaries, preferences, and entity memory. |
| `Backend/aegis_backend/chatbot_minutes/services/llm_service.py` | Added one LLM interface for Groq, Azure OpenAI, Azure AI Foundry, JSON planning, and fallback behaviour. |
| `Backend/aegis_backend/chatbot_minutes/services/query_planner.py` | Added query intent, retrieval mode, date/entity extraction, response format, and tool selection. |
| `Backend/aegis_backend/chatbot_minutes/services/grounding_service.py` | Computes confidence and flags unsupported numeric claims or potential cross-document conflicts. |
| `Backend/aegis_backend/chatbot_minutes/services/azure_search_indexer.py` | Defines/provisions the production Azure AI Search index and pushes document chunks and vectors after upload. |
| `Backend/aegis_backend/scripts/provision_minutes_chatbot_search.py` | Explicit administrator-run command to create/update the Azure AI Search index. |
| `Backend/aegis_backend/routes/auth.py` | Uses signed application session tokens after SSO callback instead of trusting a client-provided identity. |
| `Backend/aegis_backend/utils/session_token.py` | Verifies signed user tokens and accepts the legacy `SESSION_SECRET` name while migrating to `AEGIS_SESSION_SECRET`. |
| `Backend/requi.txt` | Added document-processing/Azure packages and compatible Intel macOS dependency pins. |
| `Backend/aegis_backend/utils/shared_env.py` | Central loader that forces every backend entrypoint onto the single `Backend/aegis_backend/.env` file. |
| `Frontend/src/pages/minutes-preparation/MinutesChatbot.tsx` | Rebuilt the chatbot UX: document library, document scope, evidence dialog, confidence, activity, secure Markdown, and status. |
| `Frontend/src/index.css` | Added font-loading and readable chatbot Markdown styles. |
| `Backend/aegis_backend/docs/MINUTES_CHATBOT_DEMO_ARCHITECTURE.md` | Documents the local demo architecture and run flow. |
| `Backend/aegis_backend/docs/ADVANCED_CHATBOT_IMPLEMENTATION.md` | Documents advanced capabilities, extraction decisions, Azure target architecture, and governance. |
| `CHATBOT_CHANGES_LOG.md` | Running change log and management justification, including Azure Document Intelligence. |
| `FINAL_CHATBOT_DEVELOPMENT_HANDOFF.md` | This complete implementation, deployment, and configuration handoff. |

The provided Adani font was inspected. The repository already contains the same font file and the global stylesheet loads it, so no duplicate binary was added.

## Azure configuration mapping

Use the single [`Backend/aegis_backend/.env`](Backend/aegis_backend/.env) file as the source of truth. Keep it out of git, store rotated secrets there or in VM secret storage, and let all backend components read from the same file.

| Service | Configuration | Important note |
|---|---|---|
| Azure AI Search | `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_API_KEY`, `AZURE_SEARCH_ADMIN_KEY`, `AZURE_SEARCH_INDEX_NAME` | The runtime API uses a query key; provisioning and ingestion require an admin key or managed identity. |
| Llama Maverick | `CHATBOT_LLM_PROVIDER=azure_foundry`, `AZURE_FOUNDRY_ENDPOINT`, `AZURE_FOUNDRY_DEPLOYMENT` | Use the Foundry resource base endpoint, not a trailing `/models` URL. The deployment alias must be confirmed in Azure AI Foundry. |
| GPT-4.1 mini fallback | `CHATBOT_FALLBACK_LLM_PROVIDER=azure_openai`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT_NAME` | The deployment alias is required; a model family name is not always the deployment name. |
| Cohere Embed v4 | `EMBEDDING_PROVIDER=cohere_azure` plus endpoint, key, and deployment/model alias | Confirm the embedding deployment alias and supported vector dimensions before enabling it. |
| PostgreSQL | `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT`, `POSTGRES_DATABASE_MINUTES` | Use a dedicated application database, not the shared default `postgres` database. Enable TLS. |
| Blob Storage | `AZURE_STORAGE_CONNECTION_STRING` or managed identity settings | A `*.search.windows.net` URL is Azure AI Search, not Blob Storage. A Blob endpoint/connection configuration is still needed. |
| Document Intelligence | `DOCUMENT_PROCESSOR=azure_document_intelligence`, endpoint/key | Confirm the Document Intelligence resource endpoint and obtain management approval before enabling it. |

Azure AI Foundry’s OpenAI-compatible endpoint uses the resource `/openai/v1/` base; deployments are configured separately. [Microsoft endpoint guidance](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/endpoints) supports this configuration approach.

## Production deployment order

1. Rotate every secret that was pasted into chat, then store replacements in Azure Key Vault or the VM’s protected environment.
2. Create a dedicated PostgreSQL database and least-privilege application user; do not use the default administrative database for chatbot tables.
3. Confirm the exact deployed names for Llama Maverick, GPT-4.1 mini, and Cohere Embed v4 in Azure.
4. Obtain the actual Azure Blob Storage endpoint/identity settings.
5. Update the single backend `.env` file with the confirmed Azure values and keep the file ignored by git.
6. Install backend dependencies and run the API database initialization/migrations.
7. Run `python scripts/provision_minutes_chatbot_search.py` once with the Search admin credential or managed identity.
8. Set `RETRIEVAL_BACKEND=azure_ai_search` and upload a controlled test document. Confirm owner-level isolation, retrieval, answer grounding, and audit logs.
9. Enable Azure Document Intelligence only after approval and OCR test acceptance.
10. Re-enable SSO, set `AEGIS_SESSION_SECRET`, and test login/logout, access isolation, and expired-token rejection.

## Local demo configuration

For local development keep:

```env
SSO_ENABLED=false
DATABASE_URL=sqlite:///./data/minutes_chatbot_demo.db
CHATBOT_LLM_PROVIDER=groq
EMBEDDING_PROVIDER=sentence_transformer
RETRIEVAL_BACKEND=database
DOCUMENT_PROCESSOR=local
```

Tesseract is optional for digital PDFs. To support scanned documents locally on macOS:

```bash
brew install tesseract poppler
```

The supplied statutory-auditor PDF was assessed as a native-text PDF (46 pages, approximately 58k characters); it does not need OCR. Azure Document Intelligence remains the preferred production option for difficult scans, tables, layouts, handwriting, and high-value audit records.

## Validation completed

- Backend Python sources compile successfully with `python3 -m compileall`.
- The frontend production build completed successfully with `npm run build`.
- The reference PDF extraction and page-aware chunking were checked locally.
- No Azure service was called, provisioned, or modified during this work.

## Deliberately not enabled yet

- **Email sending:** the feature should be enabled only after management chooses Microsoft Graph, Azure Communication Services, or SMTP; it must include user confirmation, recipient allow-listing, audit logging, and data-loss controls.
- **Azure Document Intelligence:** awaiting management approval and the correct resource configuration.
- **Production Azure credentials:** not inserted into tracked files or tested, because secrets must be rotated and deployment names/Blob settings are incomplete.
