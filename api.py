from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import json, os, logging, uuid

from database import get_db, create_tables, User, Report, Job
from auth import hash_password, verify_password, create_access_token, get_current_user, validate_password
from security import SecurityHeadersMiddleware, RateLimitMiddleware, sanitize_string, SafeLogger

# ── App ──
app = FastAPI(title="Account Intelligence Radar API")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

os.makedirs("reports", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Secure logging — redacts API keys
log_handler = logging.FileHandler(f"logs/api_{datetime.now().strftime('%Y%m%d')}.log")
log_handler.addFilter(SafeLogger())
stream_handler = logging.StreamHandler()
stream_handler.addFilter(SafeLogger())

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[log_handler, stream_handler]
)
logger = logging.getLogger(__name__)

# In-memory job tracker
jobs = {}

DEFAULT_OBJECTIVE = """
Extract:
- Headquarters
- Business units and services
- Core products
- Official leadership (executives only)
- Top 5 recent strategic initiatives (AI, expansion, ERP, investments)

Return structured JSON with source for every fact.
"""


# ── Models ──

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str

class CompanyRequest(BaseModel):
    company_name: str
    objective: Optional[str] = None

class GeographyRequest(BaseModel):
    country: str
    city: Optional[str] = ""
    sector: str
    objective: Optional[str] = None


# ── Startup ──

@app.on_event("startup")
def startup():
    create_tables()
    logger.info("Database ready.")


# ══════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════

@app.post("/api/auth/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    validate_password(req.password)
    sanitize_string(req.username)

    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if len(req.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")

    user = User(email=req.email, username=req.username, password=hash_password(req.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "username": user.username}
    }


@app.post("/api/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (User.email == form.username) | (User.username == form.username)
    ).first()

    if not user or not verify_password(form.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_access_token({"sub": user.id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "username": user.username}
    }


@app.get("/api/auth/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "created_at": current_user.created_at.isoformat()
    }


# ══════════════════════════════════════════
#  BACKGROUND JOBS
# ══════════════════════════════════════════

def run_company_job(job_id: str, user_id: str, company_name: str, objective: str, expected_country: str = ""):
    # Initialize in memory if missing (e.g. after restart)
    if job_id not in jobs:
        jobs[job_id] = {"status": "running", "logs": [], "mode": "company"}

    jobs[job_id]["status"] = "running"
    from database import SessionLocal
    db = SessionLocal()

    try:
        from services.serp_service import search_google
        from services.llm_selector import select_best_urls
        from services.firecrawl_service import scrape_markdown
        from services.llm_extractor import extract_structured_json
        from report_builder import save_report
        from robots_checker import filter_allowed_urls

        def log(msg):
            jobs[job_id]["logs"].append(msg)
            j = db.query(Job).filter(Job.id == job_id).first()
            if j:
                j.logs = json.dumps(jobs[job_id]["logs"])
                j.status = "running"
                db.commit()

        log(f"Searching Google for: {company_name}")
        results = search_google(company_name)
        if not results:
            raise Exception("No search results found.")

        log("Selecting best URLs with LLM...")
        urls = select_best_urls(company_name, results, objective)
        if not urls:
            raise Exception("No relevant URLs selected.")

        log(f"Checking robots.txt for {len(urls)} URLs...")
        urls = filter_allowed_urls(urls)
        if not urls:
            raise Exception("All URLs blocked.")

        jobs[job_id]["urls"] = urls
        log(f"Scraping {len(urls)} approved URLs...")
        markdown_content = scrape_markdown(urls)

        log("Running LLM extraction...")
        structured_data = extract_structured_json(company_name, markdown_content, objective, expected_country=expected_country)

        log("Saving report...")
        paths = save_report(company_name, structured_data)

        report = Report(
            user_id=user_id,
            company=company_name,
            filename=os.path.basename(paths["json"]),
            json_path=paths["json"],
            md_path=paths["markdown"],
            data=json.dumps(structured_data)
        )
        db.add(report)

        j = db.query(Job).filter(Job.id == job_id).first()
        if j:
            j.status = "done"
            j.result = json.dumps(structured_data)
            j.logs = json.dumps(jobs[job_id]["logs"] + ["Done! Report saved."])
        db.commit()

        jobs[job_id]["status"] = "done"
        jobs[job_id]["result"] = structured_data
        jobs[job_id]["paths"] = paths

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
        j = db.query(Job).filter(Job.id == job_id).first()
        if j:
            j.status = "error"
            j.error = str(e)
            db.commit()
    finally:
        db.close()


def _run_single_company_for_geography(args):
    """Helper for parallel execution in Geography Mode."""
    job_id, sub_id, user_id, company, objective, expected_country = args
    jobs[sub_id] = {"status": "pending", "logs": []}

    from database import SessionLocal
    db = SessionLocal()
    try:
        sub_job = Job(
            id=sub_id, user_id=user_id, mode="company",
            input_data=json.dumps({"company": company}),
            logs=json.dumps([])
        )
        db.add(sub_job)
        db.commit()
    finally:
        db.close()

    run_company_job(sub_id, user_id, company, objective, expected_country=expected_country)

    return {
        "company": company,
        "status": jobs[sub_id]["status"],
        "result": jobs[sub_id].get("result"),
        "paths": jobs[sub_id].get("paths"),
        "error": jobs[sub_id].get("error"),
    }


def run_geography_job(job_id: str, user_id: str, country: str, city: str, sector: str, objective: str):
    if job_id not in jobs:
        jobs[job_id] = {"status": "running", "logs": [], "mode": "geography"}

    jobs[job_id]["status"] = "running"
    jobs[job_id]["companies"] = []

    from database import SessionLocal
    db = SessionLocal()

    try:
        from services.serp_service import search_google
        from services.company_discovery import extract_company_list

        def log(msg):
            jobs[job_id]["logs"].append(msg)

        query = f"Top {sector} companies in {city} {country}".strip()
        log(f"Searching: {query}")
        results = search_google(query)
        if not results:
            raise Exception("No search results found.")

        log("Extracting company shortlist via LLM...")
        company_names = extract_company_list(results, country=country, city=city, sector=sector)
        if not company_names:
            raise Exception("No companies identified.")

        company_names = company_names[:3]
        jobs[job_id]["companies"] = company_names
        log(f"Shortlisted: {', '.join(company_names)}")

        # ── FIX 4: Run sub-jobs in parallel using ThreadPoolExecutor ──
        sub_ids = [str(uuid.uuid4()) for _ in company_names]
        args_list = [
            (job_id, sub_ids[i], user_id, company_names[i], objective, country)
            for i in range(len(company_names))
        ]

        log(f"Processing {len(company_names)} companies in parallel...")
        with ThreadPoolExecutor(max_workers=3) as executor:
            results_list = list(executor.map(_run_single_company_for_geography, args_list))

        jobs[job_id]["company_results"] = results_list
        jobs[job_id]["status"] = "done"
        log("All companies processed.")

        j = db.query(Job).filter(Job.id == job_id).first()
        if j:
            j.status = "done"
            j.logs = json.dumps(jobs[job_id]["logs"])
            db.commit()

    except Exception as e:
        logger.error(f"Geography job {job_id} failed: {e}")
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
        j = db.query(Job).filter(Job.id == job_id).first()
        if j:
            j.status = "error"
            j.error = str(e)
            db.commit()
    finally:
        db.close()


# ══════════════════════════════════════════
#  INTELLIGENCE ENDPOINTS
# ══════════════════════════════════════════

@app.post("/api/company")
def start_company(req: CompanyRequest, background_tasks: BackgroundTasks,
                  current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company_name = sanitize_string(req.company_name)
    objective = sanitize_string(req.objective) if req.objective else DEFAULT_OBJECTIVE

    job_id = str(uuid.uuid4())
    db.add(Job(id=job_id, user_id=current_user.id, mode="company",
               input_data=json.dumps({"company": company_name}), logs=json.dumps([])))
    db.commit()
    jobs[job_id] = {"status": "pending", "logs": [], "mode": "company"}
    background_tasks.add_task(run_company_job, job_id, current_user.id, company_name, objective)
    return {"job_id": job_id}


@app.post("/api/geography")
def start_geography(req: GeographyRequest, background_tasks: BackgroundTasks,
                    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    country = sanitize_string(req.country)
    city = sanitize_string(req.city) if req.city else ""
    sector = sanitize_string(req.sector)
    objective = sanitize_string(req.objective) if req.objective else DEFAULT_OBJECTIVE

    job_id = str(uuid.uuid4())
    db.add(Job(id=job_id, user_id=current_user.id, mode="geography",
               input_data=json.dumps({"country": country, "city": city, "sector": sector}),
               logs=json.dumps([])))
    db.commit()
    jobs[job_id] = {"status": "pending", "logs": [], "mode": "geography"}
    background_tasks.add_task(run_geography_job, job_id, current_user.id, country, city, sector, objective)
    return {"job_id": job_id}


# ── FIX 3: Get job from DB if not in memory (handles server restart) ──
@app.get("/api/job/{job_id}")
def get_job(job_id: str, current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db)):
    # Check memory first (live job)
    if job_id in jobs:
        return jobs[job_id]

    # Fallback to DB (after restart)
    j = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()

    if not j:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "status": j.status,
        "mode": j.mode,
        "logs": json.loads(j.logs) if j.logs else [],
        "result": json.loads(j.result) if j.result else None,
        "error": j.error,
        "created_at": j.created_at.isoformat(),
    }


@app.get("/api/reports")
def list_reports(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reports = db.query(Report).filter(
        Report.user_id == current_user.id
    ).order_by(Report.created_at.desc()).all()
    return [
        {"id": r.id, "company": r.company, "filename": r.filename,
         "created_at": r.created_at.isoformat(), "data": json.loads(r.data) if r.data else {}}
        for r in reports
    ]


@app.get("/api/reports/{report_id}")
def get_report(report_id: str, current_user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    r = db.query(Report).filter(
        Report.id == report_id,
        Report.user_id == current_user.id
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"id": r.id, "company": r.company, "filename": r.filename,
            "created_at": r.created_at.isoformat(), "data": json.loads(r.data) if r.data else {}}


@app.delete("/api/reports/{report_id}")
def delete_report(report_id: str, current_user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    r = db.query(Report).filter(
        Report.id == report_id,
        Report.user_id == current_user.id
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    db.delete(r)
    db.commit()
    return {"message": "Report deleted"}


@app.get("/api/jobs/history")
def job_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job_records = db.query(Job).filter(
        Job.user_id == current_user.id
    ).order_by(Job.created_at.desc()).limit(20).all()
    return [
        {"id": j.id, "mode": j.mode, "status": j.status,
         "created_at": j.created_at.isoformat(), "error": j.error}
        for j in job_records
    ]


# ══════════════════════════════════════════
#  PDF EXPORT — FIX 5: Font fallback
# ══════════════════════════════════════════

@app.get("/api/reports/{report_id}/pdf")
def export_pdf(report_id: str, current_user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    r = db.query(Report).filter(
        Report.id == report_id,
        Report.user_id == current_user.id
    ).first()

    if not r:
        raise HTTPException(status_code=404, detail="Report not found")

    data = json.loads(r.data) if r.data else {}
    safe_name = r.company.replace(" ", "_").replace("/", "-")
    timestamp = r.created_at.strftime("%Y%m%d_%H%M%S")
    pdf_path = f"reports/{safe_name}_{timestamp}.pdf"

    try:
        from pdf_exporter import generate_pdf
        generate_pdf(r.company, data, pdf_path)
    except FileNotFoundError as e:
        # FIX 5: Font missing — give clear error instead of crash
        raise HTTPException(
            status_code=500,
            detail="PDF fonts not found. Please add DejaVuSans.ttf and DejaVuSans-Bold.ttf to the fonts/ folder."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"{safe_name}_report.pdf"
    )


# ══════════════════════════════════════════
#  ROOT
# ══════════════════════════════════════════

@app.get("/")
def root():
    return {"message": "Account Intelligence Radar API — running ✅"}
