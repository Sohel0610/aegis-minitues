# Aegis Disclosure Intelligence: AI Chatbot Architecture

The Aegis Disclosure Chatbot is a specialized LLM-powered agent designed to sit atop the Statutory Disclosure Registry. It serves as a "Conversational Terminal" for Compliance Officers and Tech Leads to monitor and manage director-related filings.

## 1. Core Feature List

### A. Natural Language Data Retrieval
*   **Director Lookup**: "Show me the profile summary for DIN 11280634."
*   **Company Mapping**: "Which companies is Abdul Ishad Khan associated with?"
*   **Advanced Filtering**: "List all directors who are KMPs and live in Gujarat."
*   **Relative Intelligence**: "Who are the family members of Director X registered in our system?"

### B. Compliance & Statutory Monitoring
*   **KYC Tracking**: "Identify all directors whose DIR-3 KYC status is 'Sync Pending'."
*   **Filing Gap Analysis**: "Show me which directors have an MBP-1 but are missing a DIR-8 for FY 2024-25."
*   **Renewal Alerts**: "Which DINs are due for status verification in the next 30 days?"

### C. Automated Document Actions
*   **Instant Retrieval**: "Get me the latest MBP-1 for Adani Green Energy."
*   **Batch Triggers**: "Generate DIR-8 forms for all directors selected in the master list."
*   **Export Commands**: "Export an Excel of all directors associated with Adani Solar Energy Four Ltd."

### D. Conflict & Risk Detection (Red-Flagging)
*   **Cross-Holding Check**: "Are there any directors shared between Company A and Company B?"
*   **Conflict Analysis**: "Does any relative of Director Y hold a position in a subsidiary company?"

---

## 2. Integrated Visual Analytics (Graph/Chart Generation)

The chatbot will utilize the **Recharts/Chart.js** library to render interactive visualizations directly in the chat interface.

| Feature | Chart Type | Description |
| :--- | :--- | :--- |
| **DIN Health** | Pie Chart | Distribution of DIN Status (Active, Approved, Deactivated, Pending). |
| **Board Density** | Bar Chart | Top 10 directors by number of board memberships. |
| **Filing Progress** | Gauge Chart | Percentage of MBP-1 vs DIR-8 completed for the current FY. |
| **ROC Distribution** | Doughnut | Geographical distribution of companies across different RoCs. |

---

## 3. Technical Implementation Roadmap

### Phase 1: RAG Integration (Retrieval Augmented Generation)
*   Connect the chatbot to the **PostgreSQL** database using a secure metadata layer.
*   Implement **SQL-Agent** logic to translate natural language into optimized SQL queries.

### Phase 2: Tool Calling (Actionable Chat)
*   Integrate the chatbot with the `mbp1_generator.py` and `dir8_generator.py` scripts.
*   Enable the chatbot to return **StreamingResponse** download links directly in the chat bubble.

### Phase 3: Visualization Layer
*   Define a JSON-to-Graph schema. When the user asks for a report, the LLM returns a structured JSON that the frontend renders as a premium chart.

---

## 4. Example User Scenarios

**User:** "Show me a chart of our filing status for 2024-25."
**Chatbot:** *[Renders a Pie Chart showing 197 Generated vs 4 Pending]* "We are at 98% completion. 4 directors (DINs 06860381, 01896949...) are still missing data."

**User:** "Download the MBP-1 for all directors in Adani Solar Energy Four Ltd."
**Chatbot:** "Gathering 12 documents... [Processing]... [Download ZIP Link Generated]"

---
*Created by Antigravity AI for the Aegis Platform Stabilization Project.*
