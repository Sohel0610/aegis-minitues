# Advanced Minutes Chatbot: Functions, Features, and Deployment Architecture

## Current implementation

The chatbot now operates as a grounded document workspace rather than a single prompt plus vector lookup.

```text
SSO/JWT identity
  -> selected document scope
  -> query plan + entity/date/reference understanding
  -> hybrid retrieval (vector + keyword) and read-only tools
  -> relevance filtering + neighbouring chunk expansion
  -> grounded answer + numerical/conflict confidence checks
  -> answer metadata, evidence chips, session memory, and audit-ready history
```

## Functions implemented

| Capability | Function / service | Behaviour |
| --- | --- | --- |
| Query planning | `QueryPlanner.build` | Uses optional lightweight LLM JSON planning with a deterministic fallback. Extracts intent, entities, date scope, subquestions, document search query, response format, tools, and coreference indicators. |
| Coreference/rewrite | `QueryPlanner._heuristic_plan` / planner prompt | Resolves follow-up wording using recent chat context; rewrites the search request before retrieval. |
| Hybrid RAG | `HybridRetrievalService.retrieve` | Combines dense embeddings with BM25 keyword scoring, then relevance-filters candidates. Exact financial terms, dates, codes, and semantic wording are both considered. |
| Parent/sibling context | `HybridRetrievalService._expand_with_siblings` | When a relevant chunk is found, includes adjacent chunks from the same document before generating the answer. |
| Structured tools | `HybridRetrievalService.run_tools` | Read-only agenda, decision, action-item, and document-catalog tools. Tools are scoped to the authenticated user unless authorised admin access applies. |
| Conflict signal | `HybridRetrievalService.detect_potential_conflicts` | Flags conservative potential conflicting terms for review; it does not pretend to resolve a conflict. |
| Layered memory | `ChatHistoryService.get_memory_context`, `upsert_session_summary`, `remember_entities` | Keeps recent working context, summary-based episodic memory for long sessions, and lightweight entity/preference memory. |
| Context control | `ChatbotService._refresh_session_summary` | Summarises a session after the configured threshold rather than passing all raw messages forever. |
| Grounding checks | `GroundingService.assess` | Returns evidence availability, confidence, numeric-claim check, and potential-conflict status. Optional LLM faithfulness check is feature-flagged. |
| Response formatting | `ChatbotService._generate_answer` | Requests concise prose, bullet lists, or Markdown comparison tables based on the query plan. |
| Safe citations | `ChatbotService._remove_inline_citations` | Removes noisy inline `[Source ...]` text. The UI renders compact, clickable evidence chips using server-returned metadata. |
| Local/VM LLM routing | `LLMService` | Uses only the provider selected by environment variables, then one explicit fallback. Local Groq does not silently try Azure first. |
| Local/Cohere embeddings | `EmbeddingService` | Uses local Sentence Transformers in demo mode or Azure-hosted Cohere Embed v4 in VM mode. Query and document embedding input types are separated. |
| Local complex extraction | `extract_document` | Preserves PDF pages, PPT slides, Excel sheets, DOCX tables, and image OCR labels. Native text is preferred; Tesseract is used only where text is weak/missing. |
| Azure Document Intelligence path | `_extract_with_document_intelligence` | Uses `prebuilt-layout` when approved/configured. It is not called in local mode. |
| Upload status | `/api/minutes-chatbot/upload`, `/documents` | Returns extraction method, page count, warnings, indexing status, and meaningful failure state. |
| UI workspace | `MinutesChatbot.tsx` | Provides document selection, document status, source/evidence dialog, Markdown tables, confidence badge, safe activity labels, multiline composer, and session history. |

## Reference PDF assessment

`Statutory Auditor Presentation (1).pdf` is a 46-page, PowerPoint-generated audit-committee presentation. It has substantial native text, so Tesseract should **not** replace normal extraction. Tesseract is a fallback for scanned/image-only pages, embedded screenshots, and image-only slides.

Local extraction limitation: it cannot reliably reconstruct complex visual table relationships, charts, multi-column reading order, or handwritten content. Azure AI Document Intelligence `prebuilt-layout` is the production replacement because it returns text, tables, selection marks, structure, and page information for PDF and Office formats. [Microsoft layout model documentation](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/layout?view=doc-intel-4.0.0)

### Local OCR prerequisites

On macOS, install the system binaries once:

```bash
brew install tesseract poppler
```

Then keep these local settings:

```env
DOCUMENT_PROCESSOR=local
OCR_ENABLED=true
OCR_DPI=220
```

The application reports a clear extraction warning rather than silently inventing text if OCR tools are unavailable.

## Local demo configuration

```env
APP_ENV=local
SSO_ENABLED=false
DATABASE_URL=sqlite:///./data/minutes_chatbot_demo.db

CHATBOT_LLM_PROVIDER=groq
CHATBOT_LLM_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=gsk_replace_with_a_real_key

EMBEDDING_PROVIDER=sentence_transformer
EMBEDDING_MODEL_PATH=sentence-transformers/all-MiniLM-L6-v2
RETRIEVAL_BACKEND=database
DOCUMENT_PROCESSOR=local
```

## Azure VM production architecture

```text
Azure AD SSO
  -> signed Aegis JWT
  -> FastAPI chatbot API (VM)
  -> PostgreSQL: users, sessions, memory, audit metadata
  -> Azure Blob Storage: original documents
  -> async ingestion worker
       -> Azure Document Intelligence prebuilt-layout
       -> canonical chunks + page/table metadata
       -> Cohere Embed v4 through Azure AI Foundry
       -> Azure AI Search hybrid index (or pgvector)
  -> query planner / tool registry
  -> Azure Foundry primary model deployment
  -> Azure OpenAI GPT-4.1 mini fallback deployment
  -> verified response / evidence metadata
```

### Required provider configuration

Use the exact deployment names created by your Azure team; do not hard-code a public model name in source code.

The runtime uses one backend `.env` file only. Keep it ignored by git and populate the confirmed PostgreSQL host, Azure AI Search service, Foundry resource, and Azure OpenAI resource there.

### Azure service mapping and items requiring confirmation

| Supplied service | Correct application setting | Status |
| --- | --- | --- |
| `az10srchdmrcbp01.search.windows.net` | `AZURE_SEARCH_ENDPOINT` | Mapped. Use query key for runtime search and an admin key/RBAC writer identity only for provisioning/index writes. |
| Foundry `/models` resource | `AZURE_FOUNDRY_ENDPOINT` without the trailing `/models` | Mapped. Confirm the exact Llama deployment alias. |
| `az10oaidmrctbtp01.openai.azure.com` | `AZURE_OPENAI_ENDPOINT` | Mapped. Confirm the GPT-4.1 mini deployment alias. |
| `...services.ai.azure.com/models/embeddings` | Cohere deployment details | Needs confirmation. The Cohere SDK needs the deployed Cohere endpoint/model alias, not an assumed generic inference URL. |
| `...cognitiveservices.azure.com` | Document Intelligence endpoint | Needs confirmation that this resource is an Azure Document Intelligence resource. |
| supplied “blob” Search URL | Blob Storage | **Not mapped**: it is another Azure AI Search URL, not a Blob endpoint. Provide a `blob.core.windows.net` account URL/container and approved identity. |
| PostgreSQL `PGDATABASE=postgres` | `POSTGRES_DATABASE_MINUTES` | Needs confirmation/create of a dedicated minutes chatbot database. Do not use the default administrative database for production module data. |

The Foundry model deployment name must be the deployment alias, not just the catalogue model ID. Microsoft documents the stable Azure OpenAI-compatible `/openai/v1` path for Foundry models and notes that `/models` is the older inference API route. [Foundry endpoint guidance](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/endpoints), [migration guidance](https://learn.microsoft.com/en-us/azure/foundry/how-to/model-inference-to-openai-migration?view=foundry-classic).

```env
APP_ENV=azure
SSO_ENABLED=true
AEGIS_SESSION_SECRET=stored-in-key-vault

# PostgreSQL
POSTGRES_HOST=your-server.postgres.database.azure.com
POSTGRES_DATABASE_MINUTES=minutes_preparation_system
POSTGRES_USER=managed-or-service-user
POSTGRES_PASSWORD=stored-in-key-vault
POSTGRES_SSLMODE=require

# Primary Azure AI Foundry deployment (for example, your approved Llama 4 Maverick deployment)
CHATBOT_LLM_PROVIDER=azure_foundry
CHATBOT_LLM_MODEL=your-primary-deployment-name
AZURE_FOUNDRY_ENDPOINT=https://your-project.services.ai.azure.com
AZURE_FOUNDRY_API_KEY=stored-in-key-vault
AZURE_FOUNDRY_DEPLOYMENT=your-primary-deployment-name

# Explicit fallback
CHATBOT_FALLBACK_LLM_PROVIDER=azure_openai
CHATBOT_FALLBACK_LLM_MODEL=gpt-4.1-mini
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=stored-in-key-vault
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1-mini

# Embeddings and retrieval
EMBEDDING_PROVIDER=cohere_azure
COHERE_AZURE_ENDPOINT=https://your-cohere-deployment.region.models.ai.azure.com/
COHERE_API_KEY=stored-in-key-vault
COHERE_EMBED_MODEL=embed-v4.0
COHERE_EMBED_DIMENSIONS=1024
RETRIEVAL_BACKEND=azure_ai_search
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_API_KEY=stored-in-key-vault
AZURE_SEARCH_INDEX=minutes-chatbot-index

# Complex document extraction
DOCUMENT_PROCESSOR=azure_document_intelligence
DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-doc-intelligence.cognitiveservices.azure.com/
DOCUMENT_INTELLIGENCE_API_KEY=stored-in-key-vault
```

Cohere Embed v4 supports configurable output dimensions; the chosen dimension must match the Azure AI Search vector field or `pgvector` schema and must not be changed without a full reindex. Cohere documents Embed v4, Azure Foundry deployment prerequisites, and query/document input types here: [Cohere on Azure](https://docs.cohere.com/docs/cohere-on-microsoft-azure), [semantic-search example](https://docs.cohere.com/v2/docs/cohere-on-azure/azure-ai-sem-search).

### Azure AI Search index contract

The production index must contain these filterable/searchable fields:

| Field | Type / purpose |
| --- | --- |
| `id` | unique chunk key |
| `owner_user_id` | filterable identity scope; required on every query |
| `document_id`, `filename` | filterable document scope and evidence display |
| `chunk_index`, `location` | page/slide/sheet evidence location |
| `content` | searchable chunk text |
| `content_vector` | vector field with the selected Cohere dimension |
| `extraction_method`, `uploaded_at`, `classification` | governance and audit filters |

Never retrieve without the authenticated owner filter. Admin cross-user search needs a separately audited role decision.

Provision the index from a secured VM/deployment shell after setting `AZURE_SEARCH_ADMIN_KEY`:

```bash
cd Backend/aegis_backend
uv run python scripts/provision_minutes_chatbot_search.py
```

The upload flow synchronises each user-scoped chunk to this index only when `RETRIEVAL_BACKEND=azure_ai_search` is enabled.

## Email capability: production-only, approval-gated

Do not send mail merely because a model detects an email-related phrase. The tool flow should be:

```text
user asks for email
  -> assistant creates a draft and recipient suggestion from JWT/SSO identity
  -> UI displays exact subject, recipients, body, attachments, and source list
  -> user explicitly confirms
  -> backend sends through approved Microsoft Graph or Azure Communication Services
  -> immutable audit event records requester, recipient, content hash, source IDs, time, and delivery result
```

Add recipient allow-lists, DLP/classification checks, rate limits, retries, and no external-recipient default. Email is intentionally not enabled in local demo mode.

## Security and deployment controls

1. The backend now uses one `.env` file at `Backend/aegis_backend/.env`. Any credentials previously committed must be rotated and removed from repository history.
2. Keep production secrets in Azure Key Vault; prefer managed identity where the selected service supports it.
3. Use Azure AD bearer token verification and RBAC at the API boundary. Do not trust an `X-User-Email` browser header.
4. Store originals in Blob Storage; keep only structured extraction/chunk metadata in PostgreSQL/Search.
5. Run ingestion asynchronously in the VM deployment. The synchronous local flow is only for demo simplicity.
6. Add document retention, delete/reindex jobs, prompt-injection scanning, upload malware scanning, audit logs, and a regression evaluation dataset before production rollout.
7. Do not expose chain-of-thought. The UI may show safe operational status such as “Searching selected documents” and “Verifying evidence.”
