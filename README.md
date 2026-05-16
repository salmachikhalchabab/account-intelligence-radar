# Account Intelligence Radar

> **Built by Experts. Delivered with Precision.**
> A production-ready business intelligence platform that turns a company name or geography into a structured intelligence report — powered by SerpAPI, LLM, and Firecrawl.

---

## What It Does

Account Intelligence Radar automates the process of researching target companies. Given a company name or a geographic region and sector, it:

1. Searches Google for relevant sources via **SerpAPI**
2. Uses an **LLM (OpenRouter)** to select the most relevant URLs
3. Respects `robots.txt` and blocks restricted sites automatically
4. Extracts structured intelligence via **Firecrawl**
5. Saves the result as **JSON**, **Markdown**, and **PDF** reports
6. Displays everything in a **web dashboard** with user authentication

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   React Frontend                     │
│         Auth · Dashboard · Company · Geography       │
└────────────────────┬────────────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────────────┐
│                  FastAPI Backend                     │
│    Auth · Jobs · Reports · PDF Export · Security     │
└──────┬──────────────┬──────────────┬────────────────┘
       │              │              │
  SerpAPI          OpenRouter     Firecrawl
  (Discovery)    (Selection +   (Scraping)
                  Extraction)
       │              │              │
┌──────▼──────────────▼──────────────▼────────────────┐
│              SQLite Database                         │
│         Users · Reports · Jobs                      │
└─────────────────────────────────────────────────────┘
```

---

## Project Structure

```
project/
├── api.py                   # FastAPI backend — all REST endpoints
├── auth.py                  # JWT authentication + password hashing
├── database.py              # SQLAlchemy models (User, Report, Job)
├── security.py              # Rate limiting, input sanitization, headers
├── robots_checker.py        # robots.txt compliance + ToS block list
├── report_builder.py        # Saves JSON + Markdown reports
├── pdf_exporter.py          # Generates professional PDF reports
├── main.py                  # Terminal CLI (alternative to web UI)
├── config.py                # API keys and settings from .env
├── error_handler.py         # Typed error classes
├── .env                     # Your API keys (never commit)
├── .env.example             # Template for API keys
├── requirements.txt         # Production dependencies
├── requirements-test.txt    # Testing dependencies
├── pytest.ini               # Test configuration
│
├── fonts/                   # DejaVu fonts for PDF generation
│   ├── DejaVuSans.ttf
│   └── DejaVuSans-Bold.ttf
│
├── services/
│   ├── serp_service.py      # Google search via SerpAPI
│   ├── llm_selector.py      # LLM-based URL selection
│   ├── llm_extractor.py     # LLM extraction + shared call_llm()
│   ├── firecrawl_service.py # Web scraping via Firecrawl
│   └── company_discovery.py # Company name extraction (Geography Mode)
│
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_auth.py
│   ├── test_security.py
│   ├── test_llm_extractor.py
│   ├── test_report_builder.py
│   └── test_robots_checker.py
│
├── reports/                 # Auto-created — JSON + Markdown reports
├── logs/                    # Auto-created — run logs
│
└── frontend/
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx
        ├── App.css
        ├── main.jsx
        ├── AuthContext.jsx
        ├── ToastContext.jsx
        └── pages/
            ├── AuthPage.jsx
            ├── Dashboard.jsx
            ├── CompanyMode.jsx
            ├── GeographyMode.jsx
            └── ReportView.jsx
```

---

## Setup

### 1. Clone or unzip the project

```powershell
cd your-project-folder
```

### 2. Create and activate a virtual environment

```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure your API keys

```powershell
copy .env.example .env
```

Open `.env` and fill in your keys:

```env
SERPAPI_KEY=your_serpapi_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
FIRECRAWL_API_KEY=your_firecrawl_key_here
LLM_MODEL=meta-llama/llama-3.3-70b-instruct:free
SECRET_KEY=your-long-random-secret-key
```

### 5. Add fonts for PDF export

Download and place in `fonts/` folder:
- [DejaVuSans.ttf](https://github.com/dejavu-fonts/dejavu-fonts/raw/version_2_37/ttf/DejaVuSans.ttf)
- [DejaVuSans-Bold.ttf](https://github.com/dejavu-fonts/dejavu-fonts/raw/version_2_37/ttf/DejaVuSans-Bold.ttf)

---

## API Keys — Where to Get Them

| Service | Purpose | Link |
|---------|---------|------|
| SerpAPI | Google search results | https://serpapi.com |
| OpenRouter | LLM inference (URL selection + extraction) | https://openrouter.ai |
| Firecrawl | Web scraping + Markdown extraction | https://firecrawl.dev |

---

## Running the Web Application

### Backend (Terminal 1)

```powershell
uvicorn api:app --reload
```

API runs at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### Frontend (Terminal 2)

```powershell
cd frontend
npm install
npm run dev
```

Web UI runs at: `http://localhost:5173`

---

## Running the CLI (Terminal Mode)

```powershell
python main.py
```

```
===================================
     Account Intelligence Radar
===================================

Select mode:
  1) Company Mode
  2) Geography Mode
```

### Company Mode

```
Enter company name: Aramco
Use default objective? (y/n): y
```

### Geography Mode

```
Enter country: Saudi Arabia
Enter city: Riyadh
Enter target sector: energy
```

> ⚠️ Geography Mode runs multiple API calls for up to 3 companies. You will be asked to confirm before it starts.

---

## Output

Reports are saved automatically:

```
reports/
├── Aramco_20260303_142501.json    # Structured data
└── Aramco_20260303_142501.md     # Human-readable summary

logs/
└── run_20260303_142501.log       # Run log
```

### Sample JSON structure

```json
{
  "company": "Aramco",
  "headquarters": {
    "value": "Dhahran, Saudi Arabia",
    "source": "https://www.aramco.com/en/about-us"
  },
  "business_units": ["Upstream", "Downstream", "Technology"],
  "strategic_initiatives": [
    {
      "title": "AI and Digital Transformation",
      "detail": "Investment in AI-driven oil field optimization",
      "source": "https://www.aramco.com/en/news"
    }
  ]
}
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|---------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login and get JWT token |
| GET | `/api/auth/me` | Get current user info |
| POST | `/api/company` | Start a Company Mode job |
| POST | `/api/geography` | Start a Geography Mode job |
| GET | `/api/job/{id}` | Get job status and logs |
| GET | `/api/reports` | List all reports for current user |
| GET | `/api/reports/{id}` | Get specific report |
| DELETE | `/api/reports/{id}` | Delete a report |
| GET | `/api/reports/{id}/pdf` | Download report as PDF |
| GET | `/api/jobs/history` | Get job history |

---

## Security

| Layer | Implementation |
|-------|---------------|
| Authentication | JWT tokens with Argon2 password hashing |
| Rate Limiting | Per-endpoint limits (5 logins/min, 10 jobs/min) |
| Input Sanitization | XSS, SQL injection, path traversal blocking |
| Security Headers | X-Frame-Options, nosniff, XSS-Protection, no-store |
| Log Redaction | API keys and tokens automatically removed from logs |

---

## Error Handling

| Error | Message |
|-------|---------|
| No search results | "No search results found." |
| LLM 402 (no balance) | "Insufficient balance — top up your account." |
| API timeout | "Request timed out — check your connection." |
| Invalid JSON from LLM | "Could not parse JSON — retry." |
| All Firecrawl URLs fail | "All URLs failed during extraction." |
| robots.txt blocked | URL is skipped with a warning |
| Content mismatch | Company data does not match expected location |

---

## Governance & Compliance

- **robots.txt**: All URLs checked with identified User-Agent before scraping
- **ToS Block List**: 12 domains permanently blocked (LinkedIn, Facebook, X, Glassdoor, etc.)
- **Crawl-delay**: Respected between requests to the same domain
- **LinkedIn**: Blocked at two levels — keyword filter + robots_checker
- **Geographic Validation**: LLM verifies company location matches the requested region
- **No secrets in logs**: API keys are never logged or printed
- **Traceability**: Every extracted fact includes its source URL

---

## Running Tests

```powershell
pip install -r requirements-test.txt
pytest
```

Expected output: **124 passed**

### Test Coverage

| File | Tests | Coverage |
|------|-------|---------|
| test_robots_checker.py | 24 | ToS blocking, noise filtering, robots.txt |
| test_auth.py | 15 | Password hashing, JWT, validation |
| test_security.py | 20 | XSS, SQL injection, log redaction |
| test_llm_extractor.py | 12 | JSON cleaning, prompt building |
| test_report_builder.py | 12 | File saving, Markdown generation |
| test_api.py | 41 | All endpoints, auth, security headers |

---

## Limitations & Known Constraints

- Geography Mode is limited to **3 companies** per run to control API costs
- LLM content extraction is capped at **12,000 characters** per scrape
- The tool does not scrape LinkedIn under any circumstances
- PDF export requires DejaVu fonts in the `fonts/` folder

---

## What I Would Improve Next

- Add Celery + Redis for a proper job queue (currently uses FastAPI BackgroundTasks)
- Add SerpAPI result caching to avoid duplicate searches
- Support batch input via CSV file
- Add confidence scoring per extracted fact
- Deploy to cloud (Render / Railway) with PostgreSQL

---

## Demo Video

▶️ Watch the full demo: [Account Intelligence Radar — Live Demo](https://www.loom.com/share/6a7f7c3f93e34643831cfc17b190cd0e)

---

## Author

**Salma Chikh Alchabab**

May 2026
