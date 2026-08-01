# 📋 Aegis Phase 3: Full-Stack Implementation Roadmap

This document outlines the scope of work for the Full-Stack engineering roadmap (excluding AI/LLM components). It serves as a persistent context log for developers and AI agents working on this workspace across sessions.

---

## 1. Vertical & Company-Wise Hierarchy (Core Architecture)
*   **Database Integration (Task 1):** ✅ **COMPLETED**
    *   *Description:* Scope all existing tables (directors, disclosures, generated minutes, compliances, locations) by `vertical_id` and `company_id`.
    *   *Current Codebase Status:* Database schema updated with `vertical_id`, `company_id`, and `secretary_name`. 21 business verticals and 1,190 companies stored.
*   **Vertical Navigation UI (Task 2):** ✅ **COMPLETED**
    *   *Description:* Vertical-wise header selector allowing paginated, searchable navigation for large company lists (200+ companies per vertical).
    *   *Current Codebase Status:* Implemented `VerticalContext.tsx` and `VerticalNavigationHeader.tsx` integrated with `ProductDashboardLayout.tsx` and `Step0TemplateCompany.tsx`.
*   **Data Migration (Task 4):** ✅ **COMPLETED**
    *   *Description:* Write a database migration script to align current flat records with the new `vertical_id` and `company_id` columns.
    *   *Current Codebase Status:* Migration completed via `d:\MOM\Backend\migrate_excel_to_db.py` from `Vertical and Entity name.xlsx` (852 records migrated, 21 verticals mapped).

---

## 2. Document Repository & Parser Pipeline
*   **Upload Module & Storage (Tasks 6 & 8):**
    *   *Description:* Drag-and-drop file upload UI and backend APIs to upload and parse digital PDFs, Word docs (`.docx`), and PowerPoint presentations (`.pptx`).
    *   *Current Codebase Status:* Basic transcript upload exists for AI processing, but a general company-wise document repository is missing. Word parser exists; PPTX parser does not.
*   **OCR Ingestion Pipeline (Task 7):**
    *   *Description:* Integrate Tesseract OCR or a similar local package in Python to extract raw text from scanned PDF meeting/resolution documents.
    *   *Current Codebase Status:* No OCR library or extraction route is configured.

---

## 3. Secretarial Compliance KPIs
*   **KPI Calculation Engine (Task 10):**
    *   *Description:* Compute compliance analytics via PostgreSQL, such as:
        *   Director meeting attendance rates.
        *   Filing timeline compliance (upcoming vs. overdue statutory forms).
        *   Meeting frequencies per company.
    *   *Current Codebase Status:* Missing. Only static seeded tables are queried.
*   **Compliance Dashboard UI (Task 11):**
    *   *Description:* Update [SecretarialCompliances.tsx](file:///d:/MOM/Frontend/src/pages/minutes-preparation/SecretarialCompliances.tsx) to query the new KPI backend APIs and render dynamic cards, charts, and tables.
    *   *Current Codebase Status:* Basic UI exists with mock numbers.

---

## 4. MS Teams & Microsoft Graph Integration
*   **Bot-as-Participant (Task 12):**
    *   *Description:* Write a Python service using the Microsoft Graph API to command a bot to join a Teams meeting using a user-provided Teams link.
    *   *Current Codebase Status:* Missing.
*   **Transcript Retrieval (Task 13):**
    *   *Description:* Integrate Microsoft Graph API Oauth credentials in the backend to pull continuous (live) or post-meeting recorded transcripts.
    *   *Current Codebase Status:* Missing.
*   **MOM Storage & Display (Task 16):**
    *   *Description:* Store transcripts linked to meetings and display them side-by-side with generated MOMs in the frontend.
    *   *Current Codebase Status:* Generated minutes files are saved flat in PostgreSQL but lack transcript pairing.
*   **MOM Email Delivery (Task 15):**
    *   *Description:* Connect to the existing SMTP mailer service to automatically distribute generated minutes to stakeholders post-meeting.
    *   *Current Codebase Status:* Missing.

---

## 5. Template Resolution & Attendance Tab
*   **Structured Table Preservation (Tasks 18 & 19):**
    *   *Description:* Capture table-formatted inputs in the template resolution editor, store them as structured JSON (rows/columns) in the database, and render them in clean HTML tables in the UI.
    *   *Current Codebase Status:* Missing. Resolutions are processed as flat text block replacements.
*   **DIN–CIN Cross-Linking (Task 20):**
    *   *Description:* Filter the attendee checklist in [Step2Attendance.tsx](file:///d:/MOM/Frontend/src/pages/minutes-preparation/components/form-steps/Step2Attendance.tsx) using active company board members queried from the Directors database by CIN/DIN.
    *   *Current Codebase Status:* Uses a [MultiDirectorSelector.tsx](file:///d:/MOM/Frontend/src/components/MultiDirectorSelector.tsx) dropdown that queries a flat master list of all directors.
*   **Template Sequencing UI (Task 21):**
    *   *Description:* Create a drag-and-drop or checklist UI in the Template Resolutions page to configure the order/sequencing of clauses and sections before generating a document.
    *   *Current Codebase Status:* Missing.

---

## 6. Minutes File Storage & Search
*   **Structured Path Storage (Task 23):**
    *   *Description:* Implement backend file-saving logic that saves generated `.docx` files in nested folders on disk following:
        `Vertical (BU) / Company Name / Meeting / Meeting Type / Year / file.docx`
    *   *Current Codebase Status:* Saved in a flat `public/templates` directory.
*   **Folder-Tree Explorer UI (Task 24):**
    *   *Description:* React-based directory tree component allowing users to browse, search, and download generated minutes through the hierarchical folder structure.
    *   *Current Codebase Status:* Missing. Only a flat history table exists.
*   **Keyword & Title Search (Task 22):**
    *   *Description:* Build SQL text search query in backend to find minutes and templates matching user keywords or titles.
    *   *Current Codebase Status:* Simple title-only filters are used.
