# AI Data Analyst

Upload a CSV. Get instant KPIs, charts, and natural language insights - powered by local LLMs and pandas.

This is a full-stack application that separates **computation** (pandas) from **interpretation** (LLM). No data is sent to external APIs. Everything runs locally via Ollama.

---

## Features

- **CSV Upload & Auto-Profiling** - Upload any CSV. Column types, missing values, outliers, and data quality scores are computed immediately.
- **AI-Powered Insights** - pandas computes all metrics; the LLM only summarizes. Zero hallucination risk for numerical data.
- **Natural Language Q&A** - Ask questions about your data in plain English. Gets answered from pre-computed aggregates.
- **Multi-Model Support** - Switch between TinyLlama, Phi-3, or Qwen2.5-Coder without restarting.
- **Model Comparison** - Compare responses and latency across models for the same question.
- **Data Quality Scoring** - Detects duplicate rows, missing values, outliers, truncated data, and case-insensitive column collisions.
- **Auto-Generated Charts** - Bar charts (regions), line charts (trends), pie charts (distributions) via matplotlib.
- **PDF Export** - Export insights, KPIs, recommendations, and charts as a single PDF.
- **Agent Workflow Visualization** - Real-time pipeline status with polling-based UI updates.
- **JWT Authentication** - Signup, login, and token-based protected routes.
- **Analysis History** - Per-user history of uploaded files and Q&A sessions.
- **Docker Support** - Multi-container orchestration with PostgreSQL, Flask, and Vite dev server.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19, React Router 6, Axios, Tailwind CSS, Vite |
| **Backend** | Python 3.12, Flask, SQLAlchemy, Flask-JWT-Extended, Flask-Migrate, Flask-CORS |
| **LLM** | Ollama (local), LangChain-Ollama, Sentence Transformers |
| **Data** | pandas, NumPy, matplotlib |
| **Vector Store** | FAISS (Facebook AI Similarity Search) |
| **Database** | SQLite (dev) / PostgreSQL (production) |
| **Infrastructure** | Docker, Docker Compose |

---

## Architecture

```
┌──────────────┐      ┌───────────────────────────────────────┐      ┌──────────┐
│   React App  │─────▶│          Flask Backend                │─────▶│  Ollama  │
│  (Vite +     │      │                                       │      │ (Local   │
│   Tailwind)  │◀────│  Routes → Middleware → Services → DB  │◀────│   LLM)   │
└──────────────┘      └───────────────────────────────────────┘      └──────────┘
                              │
                              ▼
                        ┌──────────┐
                        │  pandas  │
                        │ (Computation)
                        └──────────┘
```

### Design Philosophy: "Pandas Calculates, LLM Explains"

The LLM never performs arithmetic or statistical computation. All numerical work is done by pandas vectorized operations:

```
CSV Upload
    │
    ▼
pandas: detect_columns() → generate_kpis() → group_by_region/dept/month() → summary_stats()
    │
    ├──▶ matplotlib generates charts from pre-computed data
    │
    └──▶ LLM receives ONLY structured JSON (KPIs + grouped metrics)
         LLM outputs: natural language insights + recommendations
```

This guarantees:
- **Zero numerical hallucination** - the LLM cannot invent numbers it didn't receive
- **Deterministic results** - same CSV always produces identical KPIs and charts
- **Fast answers** - common questions (top regions, trends, distributions) are answered from cached aggregates without an LLM call

### Project Structure

```
backend/                     # Flask application
├── app.py                   # Application factory, blueprint registration
├── config/
│   └── config.py            # Environment-based configuration
├── extensions.py            # Flask extension initialization (db, migrate, jwt)
├── middleware/
│   ├── auth_middleware.py   # JWT token verification decorator
│   └── logging_middleware.py# Request/response logging with timing
├── models/
│   ├── user.py              # User model (id, name, email, password_hash)
│   ├── upload.py            # Upload tracking model
│   └── analysis_history.py  # Q&A session history model
├── routes/
│   ├── auth_routes.py       # /api/auth/* - signup, login, profile
│   ├── upload_routes.py     # /api/uploads/* - CSV upload, list
│   ├── analysis_routes.py   # /api/analysis/* - insights, QA, quality, charts, models
│   └── history_routes.py    # /api/history/* - user analysis history
├── services/
│   ├── analysis_service.py  # Core pandas pipeline (KPI, aggregation, stats)
│   ├── ai_service.py        # LLM orchestration with caching, retry, safety guard
│   ├── auth_service.py      # Password hashing and JWT token generation
│   ├── chart_service.py     # matplotlib chart generation
│   ├── llm_service.py       # Ollama model management (singleton per model)
│   ├── pandas_analysis.py   # Lightweight keyword-based row filtering
│   └── upload_service.py    # File persistence and path resolution
├── utils/
│   ├── data_profile.py      # Missing values, outliers, correlations, quality scoring
│   ├── file_helpers.py      # Sanitized filename generation
│   ├── prompt_builder.py    # Mode-based prompt construction (executive, technical, concise, etc.)
│   ├── prompts.py           # Domain-specific prompt templates
│   ├── rag.py               # FAISS vector store with high-signal row selection
│   ├── response_helpers.py  # Standardized JSON responses, exception hierarchy, error handlers
│   └── validators.py        # Decorator-based input validation
├── Dockerfile
└── requirements.txt

frontend/                    # React application
├── src/
│   ├── api/api.js           # Axios client with JWT interceptor
│   ├── context/AuthContext.jsx  # Auth state management
│   ├── pages/
│   │   ├── Dashboard.jsx    # Main dashboard (10 views, PDF export)
│   │   ├── Login.jsx
│   │   ├── Signup.jsx
│   │   └── History.jsx
│   └── components/
│       ├── analysis/        # KPICards, QuestionSection
│       ├── charts/          # ChartDisplay
│       ├── layout/          # ProtectedRoute
│       ├── prompt/          # PromptPlayground
│       ├── upload/          # UploadSection
│       └── workflow/        # AgentWorkflow (realtime pipeline visualization)
├── vite.config.js
├── tailwind.config.js
└── package.json
```

---

## API Overview

All endpoints return a consistent JSON envelope:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "timestamp": "2026-07-02T10:30:00.123456"
}
```

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/auth/signup` | POST | No | Create account |
| `/api/auth/login` | POST | No | Get JWT token |
| `/api/auth/me` | GET | Yes | Current user profile |
| `/api/uploads` | POST | Yes | Upload CSV file |
| `/api/uploads` | GET | Yes | List user uploads |
| `/api/analysis/insights` | POST | Yes | Full pipeline: pandas → charts → LLM |
| `/api/analysis/ask` | POST | Yes | Natural language Q&A |
| `/api/analysis/quality` | POST | Yes | Data quality scoring |
| `/api/analysis/profile` | POST | Yes | Data profiling |
| `/api/analysis/recommend` | POST | Yes | AI recommendations |
| `/api/analysis/model` | GET/POST | Yes | Model configuration |
| `/api/analysis/compare-models` | POST | Yes | Cross-model comparison |
| `/api/analysis/status` | GET | Yes | Pipeline status |
| `/api/analysis/architecture` | GET | Yes | System metadata |
| `/api/history/uploads` | GET | Yes | Upload history |
| `/api/history/analysis` | GET | Yes | Analysis history |
| `/api/health` | GET | No | Health check |

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.ai) installed and running
- At least one model pulled: `ollama pull tinyllama`

### Quick Start (Local)

```bash
# 1. Backend
cd backend
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py               # Runs on http://localhost:5000

# 2. Frontend (separate terminal)
cd frontend
npm install
npm run dev                 # Runs on http://localhost:5173
```

### Docker

```bash
docker compose up --build
```

This starts Postgres, Flask (port 5000), and Vite dev server (port 5173).

### Generate Sample Data

```bash
python sample_data.py
# Creates sales_dataset_10.csv with 1000 synthetic rows
```

---
## Use Cases

- **Business analysts** who want quick insights from CSV exports without writing SQL or Python
- **Data exploration** - upload an unfamiliar dataset and get an immediate summary of structure, quality, and key metrics
- **LLM evaluation** - compare TinyLlama, Phi-3, and Qwen2.5-Coder on data interpretation tasks
- **Educational** - demonstrates the "pandas computes, LLM explains" pattern for reliable AI-assisted analytics

---

## Future Improvements

- [ ] **Large file streaming** - process datasets exceeding available memory via chunked pandas read
- [ ] **Custom visualization** - allow users to specify chart type and axes
- [ ] **Conversation memory** - persistent per-session chat across page reloads
- [ ] **Multi-file workspaces** - upload and compare multiple datasets
- [ ] **SQL export** - generate SQL queries from natural language questions
- [ ] **Scheduled analysis** - periodic re-analysis of updated data sources
- [ ] **Role-based access** - admin, analyst, viewer permission levels
- [ ] **API token management** - programmatic access for external tools

---

## License

MIT
