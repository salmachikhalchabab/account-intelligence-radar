# Account Intelligence Radar

> **Built by Experts. Delivered with Precision.**  
> A production-ready research tool that turns a company name or geography into an actionable intelligence report — ready for business outreach.

---

## What It Does

Account Intelligence Radar automates the process of researching target companies. Given a company name or a geographic region and sector, it:

1. Searches Google for relevant sources via **SerpAPI**
2. Uses an **LLM (OpenRouter)** to select the most relevant URLs
3. Respects `robots.txt` and blocks LinkedIn automatically
4. Extracts structured intelligence via **Firecrawl**
5. Saves the result as both **JSON** and **Markdown** reports

---

## Project Structure

```
project/
├── main.py                  # Entry point — run this
├── config.py                # API keys and settings
├── error_handler.py         # Typed error handling
├── robots_checker.py        # robots.txt compliance + LinkedIn block
├── report_builder.py        # Saves JSON + Markdown reports
├── .env                     # Your API keys (never commit this)
├── .env.example             # Template for API keys
├── requirements.txt         # Python dependencies
├── reports/                 # Auto-created — stores JSON + Markdown reports
├── logs/                    # Auto-created — stores run log files
└── services/
    ├── serp_service.py      # Google search via SerpAPI
    ├── llm_selector.py      # LLM-based URL selection
    ├── llm_extractor.py     # LLM extraction + shared call_llm()
    ├── firecrawl_service.py # Web scraping via Firecrawl
    └── company_discovery.py # Company name extraction (Geography Mode)
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

Copy `.env.example` to `.env` and fill in your keys:

```powershell
copy .env.example .env
```

Then open `.env` and add your keys:

```env
SERPAPI_KEY=your_serpapi_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
FIRECRAWL_API_KEY=your_firecrawl_key_here
LLM_MODEL=arcee-ai/trinity-large-preview:free
```

---

## API Keys — Where to Get Them

| Service | Purpose | Link |
|---------|---------|------|
| SerpAPI | Google search results | https://serpapi.com |
| OpenRouter | LLM inference (URL selection + extraction) | https://openrouter.ai |
| Firecrawl | Web scraping + Markdown extraction | https://firecrawl.dev |

---

## Running the Tool

```powershell
python main.py
```

You will be prompted to choose a mode:

```
===================================
     Account Intelligence Radar
===================================

Select mode:
  1) Company Mode
  2) Geography Mode
```

### Company Mode

Enter a company name and an objective. Example:

```
Enter company name: Aramco
Use default objective? (y/n): y
```

### Geography Mode

Enter a country, city, and sector. Example:

```
Enter country: Saudi Arabia
Enter city: Riyadh
Enter target sector: energy
```

> ⚠️ Geography Mode runs multiple API calls (SerpAPI + LLM + Firecrawl) for up to 3 companies. You will be asked to confirm before it starts.

---

## Output

Reports are saved automatically in the `reports/` folder, and logs in the `logs/` folder:

```
reports/
├── Aramco_20260303_142501.json      # Structured data
└── Aramco_20260303_142501.md        # Human-readable summary

logs/
└── run_20260303_142501.log          # Run log
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

## Error Handling

The tool handles all major failure modes gracefully:

| Error | Message |
|-------|---------|
| No search results | "No search results found." |
| LLM 402 (no balance) | "Insufficient balance — top up your account." |
| API timeout | "Request timed out — check your connection." |
| Invalid JSON from LLM | "Could not parse JSON — retry." |
| All Firecrawl URLs fail | "All URLs failed during extraction." |
| robots.txt blocked | URL is skipped with a warning |

---

## Governance & Compliance

- **robots.txt**: All URLs are checked before scraping. Blocked URLs are skipped.
- **LinkedIn**: Blocked at two levels — keyword filter in SerpAPI results, and explicit check in robots_checker.
- **No secrets in logs**: API keys are never logged or printed.
- **Traceability**: Every extracted fact includes its source URL.

---

## Limitations & Known Constraints

- Geography Mode is limited to **3 companies** per run to control API costs.
- LLM content extraction is capped at **12,000 characters** per scrape to stay within model context limits.
- The tool does not scrape LinkedIn under any circumstances.

---

## Author

**Salma Chikh Alchabab**  
Internal — Averroa  
March 2026
