# InsightFlow AI — Autonomous Business Data Analyst 🚀

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%2019%20%2B%20Vite-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS%20v4-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Recharts](https://img.shields.io/badge/Charts-Recharts-22b5bf?style=flat-square)](https://recharts.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

An enterprise-grade, full-stack **Autonomous AI Business Data Analyst Platform**. Upload tabular datasets (CSV, Excel, JSON) to immediately receive automated statistical profiling, zero-hallucination exploratory data analysis (EDA), multivariate correlation matrices, predictive forecasting, dynamic interactive charts, and natural language conversational querying.

---

## ✨ Key Features

- 📊 **Autonomous Statistical Profiling**: Ingests raw tabular data and dynamically computes column summaries, moments, quantiles, missingness rates, and data quality indexes.
- 💬 **Ask Your Data (AI Analyst Chat)**: Conversational natural language querying with Python-verified facts, automated analytical SQL generation, and dynamic chart rendering.
- 📈 **Dynamic Multivariate Charts**: Interactive Line, Bar, Area, Donut, and Scatter plots powered by Recharts with multi-dimensional filtering, theme customization, and CSV export.
- 🎯 **Anomaly & Outlier Detection**: Automated $1.9\sigma$ to $3.0\sigma$ Z-score anomaly scanning and IQR outlier flagging.
- 🔮 **Predictive Time-Series Forecasting**: Exponential smoothing & Holt-Winters trend modeling with confidence bands and interactive What-If scenario simulations.
- 📑 **Automated Executive Reports**: Generates structured business intelligence digests and summaries ready for stakeholders.
- 🔒 **Enterprise Security & Zero Leakage**: Strictly segregated secrets, parameterized CORS, client-side token management, and OWASP security headers.

---

## 🏗️ System Architecture

```
├── Business-data-analyst/     # Frontend (React 19, Vite, Tailwind CSS v4, Lucide, Recharts)
│   ├── src/
│   │   ├── components/        # Charts, Chat, KPIs, Tables, Modals, Layout
│   │   ├── views/             # Dashboard, Analytics, Chat, Datasets, Forecast, Reports
│   │   ├── services/          # Centralized API Client & Supabase integrations
│   │   ├── context/           # App state management
│   │   └── utils/             # Data engine & statistical helpers
│   ├── vercel.json            # Vercel SPA routing configuration
│   └── package.json
│
├── backend/                   # Backend (Python 3.10+, FastAPI, Pandas, NumPy, Uvicorn)
│   ├── app/
│   │   ├── agents/            # Specialized Analytics & EDA AI Agents
│   │   ├── api/v1/endpoints/  # Datasets, Chat, Predictions, Visualizations, Reports
│   │   ├── core/              # Config, Security, Rate Limiter, Structured Logging
│   │   ├── schemas/           # Pydantic data contracts
│   │   └── services/          # Data processing & storage pipelines
│   ├── tests/                 # Automated Pytest suite
│   └── pyproject.toml
│
├── run_backend.bat            # Quick startup script for FastAPI backend
├── run_frontend.bat           # Quick startup script for Vite frontend
└── README.md
```

---

## 🚀 Quick Start (Local Setup)

### Prerequisites
- **Node.js**: v18.0 or higher
- **Python**: v3.10 or higher
- **Git**

---

### 1. Clone the Repository
```bash
git clone https://github.com/JatinAgrawal001/Business-data-analyst.git
cd Business-data-analyst
```

---

### 2. Backend Setup (FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -e .

# Configure environment variables
cp .env.example .env

# Start FastAPI server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be live at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### 3. Frontend Setup (React + Vite)

Open a new terminal window:
```bash
cd Business-data-analyst

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env

# Start development server
npm run dev
```
The application will open at: [http://localhost:5173](http://localhost:5173)

---

## ⚙️ Environment Variables

### Backend (`backend/.env`)
| Variable | Description | Default |
|---|---|---|
| `PROJECT_NAME` | Name of the application | `InsightFlow Analytics API` |
| `ENVIRONMENT` | Runtime environment | `development` |
| `API_V1_STR` | API prefix | `/api/v1` |
| `CORS_ORIGINS` | Allowed frontend origins | `["http://localhost:5173","http://localhost:3000"]` |
| `CORS_ALLOW_ORIGIN_REGEX` | Regex for allowed origins | `^https?://(localhost\|127\.0\.0\.1)(:\d+)?$` |
| `SUPABASE_URL` | Supabase project URL | `Your Supabase URL` |
| `SUPABASE_KEY` | Supabase publishable anon key | `Your Anon Key` |
| `NVIDIA_API_KEY` | Optional NVIDIA NIM API key | `""` |

### Frontend (`Business-data-analyst/.env`)
| Variable | Description |
|---|---|
| `VITE_API_URL` | URL of the FastAPI Backend (`http://localhost:8000/api/v1`) |
| `VITE_SUPABASE_URL` | Supabase Project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase Anon Key |

> ⚠️ **Security Notice**: Never commit `.env` files containing private keys or credentials to version control. All `.env` files are ignored by default in `.gitignore`.

---

## 🌐 Deployment Guide

### Deploying Frontend to Vercel
1. Link your GitHub repository in [Vercel](https://vercel.com).
2. Set **Root Directory** to `Business-data-analyst`.
3. Set **Framework Preset** to `Vite`.
4. Add environment variables: `VITE_API_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`.
5. Deploy!

### Deploying Backend to Render / Railway / Cloud Run
1. Create a new Web Service on [Render](https://render.com).
2. Set **Root Directory** to `backend`.
3. Set **Build Command**: `pip install -e .`
4. Set **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Configure your CORS origins to allow your live Vercel domain.

---

## 🧪 Testing

Run backend automated tests:
```bash
cd backend
pytest tests/ -v
```

---

## 📄 License
This project is open source and available under the [MIT License](LICENSE).
