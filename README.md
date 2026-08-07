# 🛡️ Aegis: Regulatory Intelligence Suite
### *High-Fidelity Compliance & Monitoring Analytics*

**Aegis** is an elite regulatory monitoring platform designed for the automated tracking and analysis of financial notifications from **BSE, SEBI, and RBI**. It features a modern, digital-first interface that synthesizes complex data into actionable intelligence.

---

## 💎 The Digital Modern UI/UX
Aegis is engineered with a **Premium UI/UX** philosophy, focusing on clarity, speed, and visual impact.
- **Vibrant Real-Time Dashboards**: Powered by **Framer Motion** for smooth, meaningful animations.
- **Glassmorphic Data Visualization**: High-fidelity charts using **Recharts** with translucent layering.
- **Optimized Cognitive Load**: A structured, dark-and-vibrant aesthetic that prioritizes critical information.
- **Intelligent Grid Systems**: Dynamic cards and stats tiles providing an instant snapshot of regulatory health.

---

## 🏗️ System Architecture & Folder Hierarchy

The project is architected as a clean, decoupled monorepo, optimized for deployment and scalability.

### 📱 **Frontend: The Visual Core** (`/Frontend`)
Built with **React 18**, **TypeScript**, and **Vite**, the frontend is designed for sub-second responsiveness.

```text
/Frontend
├── src/
│   ├── pages/             # Domain-specific dashboards (BSE, RBI, SEBI, Insider Trading)
│   ├── components//       # Organized component library
│   │   ├── charts/        # Custom high-fidelity charts (Trends, Pie, Line)
│   │   ├── ui/            # shadcn/ui base components
│   │   └── layout/        # Responsive structural wrappers
│   ├── hooks/             # Specialized React logic and data fetching
│   ├── lib/               # Utility functions and API clients
│   └── types/             # Strict TypeScript definitions
├── public/                # Static assets and icons
├── package.json           # Modern build configuration
├── vite.config.ts         # Vite orchestration
└── tailwind.config.ts     # Design system tokens
```

### 🧠 **Backend: The Intelligence Core** (`/Backend`)
The **FastAPI-driven** backend provides high-performance asynchronous data serving and AI orchestration.

```text
/Backend
├── aegis_backend/         # Primary API Service
│   ├── routes/            # Specialized API handlers (BSE, RBI, SEBI, Insider Trading)
│   ├── public/            # Persistence layer (SQLite Databases)
│   ├── scripts/           # Data migration and processing tools
│   └── fastapi_server.py  # Core entry point
├── chatbot_backend/       # AI & RAG Service
│   ├── llm_layer/         # LLM integration (Azure/Groq)
│   └── indexing_layer/    # Document vectorization for AI chat
├── venv/                  # Python Virtual Environment
├── start-dev.bat          # Unified development startup
├── start-app.bat          # Production-ready startup script
└── start-dev.py           # Cross-platform orchestration script
```

---

## 🧩 Functional Module Matrix

### 📊 **BSE Intelligence**
- **Automated Alerts**: Captures intsintations with a **10,000 record capacity**, supporting multi-year historical analysis.
- **Interactive Dashboards**: Features **Daily, Weekly, and Monthly Trend Charts** for volatility tracking.

### 🏦 **RBI Compliance Engine**
- **Circular Monitoring**: Tracks all RBI circulars with direct PDF linkage.
- **Hierarchical Layouts**: Organizes regulatory data by banking category and significance.

### ⚖️ **SEBI Regulation Hub**
- **Analysis Dashboards**: Visualizes SEBI regulatory shifts through specialized charts.
- **Direct Interfacing**: Seamless integration with the SEBI database for real-time document retrieval.

### 🕵️ **Insider Trading Oversight**
- **Movement Analytics**: Tracks buyers, sellers, and major exits within the ecosystem.
- **Depository Tracking**: Specialized data streams from **CDSL, NSDL, and Physical** holdings.
- **Trend Visualization**: Integrated KPIs for net shares and investor count changes.

### 🤖 **AI Assistant & Document RAG**
- **Contextual Search**: Chat directly with regulatory documents.
- **Instant Summarization**: Distills voluminous disclosures into crisp, professional summaries using Advanced LLMs.

---

## 🛠️ Operational Guide

### 1. Launching the Environment
Aegis provides specialized scripts for centralized management. From the **Backend** folder:
- **`start-dev.bat`**: Runs the FastAPI server and the React dev server concurrently.
- **`start-app.bat`**: Professional startup with Nginx/SSL integration.

### 2. Manual Execution
**Backend**:
```bash
cd Backend
python aegis_backend/fastapi_server.py
```
**Frontend**:
```bash
cd Frontend
npm run dev
```

---
*Aegis: Defining the future of Regulatory Monitoring.*