import json
import logging
import os
from datetime import datetime

from services.serp_service import search_google
from services.llm_selector import select_best_urls
from services.firecrawl_service import scrape_markdown
from services.llm_extractor import extract_structured_json
from services.company_discovery import extract_company_list
from report_builder import save_report
from error_handler import handle_error
from robots_checker import filter_allowed_urls


# ===============================
# Logging Setup
# ===============================

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"logs/run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# ===============================
# Default Objective
# ===============================

DEFAULT_OBJECTIVE = """
Extract:
- Headquarters
- Business units and services
- Core products
- Official leadership (executives only)
- Top 5 recent strategic initiatives (AI, expansion, ERP, investments)

Return structured JSON with source for every fact.
"""


# ===============================
# Core Processing Logic
# ===============================

def process_single_company(company_name: str, objective: str):

    logger.info(f"Starting processing for: {company_name}")
    print(f"\n--- Processing: {company_name} ---")

    results = search_google(company_name)

    if not results:
        logger.warning(f"No search results found for: {company_name}")
        print("No search results found.")
        return

    # Select best URLs
    urls = select_best_urls(company_name, results, objective)

    if not urls:
        logger.warning(f"No relevant URLs selected for: {company_name}")
        print("No relevant URLs selected.")
        return

    print("\nSelected URLs before robots check:")
    for i, url in enumerate(urls, 1):
        print(f"  {i}. {url}")

    # Robots filtering
    urls = filter_allowed_urls(urls)

    if not urls:
        logger.warning(f"All URLs blocked by robots.txt for: {company_name}")
        print("No URLs allowed after robots filtering.")
        return

    print("\nURLs approved for extraction:")
    for i, url in enumerate(urls, 1):
        print(f"  {i}. {url}")

    # Scrape
    logger.info(f"Scraping {len(urls)} URLs for: {company_name}")
    print("\nScraping content...")
    markdown_content = scrape_markdown(urls)

    # LLM Extraction
    logger.info(f"Running LLM extraction for: {company_name}")
    structured_data = extract_structured_json(company_name, markdown_content, objective)

    # Save JSON + Markdown
    paths = save_report(company_name, structured_data)

    # Display output
    print("\n==============================")
    print(" Structured Intelligence Output")
    print("==============================\n")
    print(json.dumps(structured_data, indent=2, ensure_ascii=False))

    print("\n------------------------------")
    print(" Report saved to:")
    print(f"  JSON:     {paths['json']}")
    print(f"  Markdown: {paths['markdown']}")
    print("------------------------------\n")

    logger.info(f"Report saved — JSON: {paths['json']} | Markdown: {paths['markdown']}")


# ===============================
# Company Mode
# ===============================

def run_company_mode():

    company_name = input("\nEnter company name: ").strip()

    print(f"\nThis is the default prompt if you want to use it:\n{DEFAULT_OBJECTIVE}")
    use_default = input("Use default objective? (y/n): ").strip().lower()

    objective = DEFAULT_OBJECTIVE if use_default == "y" else input("\nEnter your custom objective:\n")

    try:
        process_single_company(company_name, objective)
    except Exception as e:
        logger.error(f"Error in Company Mode: {e}")
        handle_error(e)


# ===============================
# Geography Mode
# ===============================

def run_geography_mode():

    country = input("\nEnter country: ").strip()
    city = input("Enter city (optional): ").strip()
    sector = input("Enter target sector (e.g. manufacturing, energy): ").strip()

    # Cost confirmation
    print("\n⚠  Geography Mode will run multiple company searches and LLM calls.")
    print("   This may consume significant API credits (SerpAPI + Groq + Firecrawl).")
    confirm = input("   Are you sure you want to continue? (y/n): ").strip().lower()

    if confirm != "y":
        print("Geography Mode cancelled.")
        logger.info("Geography Mode cancelled by user.")
        return

    print(f"\nThis is the default prompt if you want to use it:\n{DEFAULT_OBJECTIVE}")
    use_default = input("Use default objective? (y/n): ").strip().lower()
    objective = DEFAULT_OBJECTIVE if use_default == "y" else input("\nEnter your custom objective:\n")

    query = f"Top {sector} companies in {city} {country}".strip()

    try:
        logger.info(f"Geography Mode — query: {query}")
        print("\nSearching for companies...")
        results = search_google(query)

        if not results:
            print("No search results found.")
            return

        print("Extracting company shortlist via LLM...")
        company_names = extract_company_list(results, country=country, city=city, sector=sector)

        if not company_names:
            print("No companies identified.")
            return

        # Limit to 3 for cost control
        company_names = company_names[:3]

        print(f"\nShortlisted companies:")
        for i, name in enumerate(company_names, 1):
            print(f"  {i}. {name}")

        for company in company_names:
            try:
                process_single_company(company, objective)
            except Exception as e:
                logger.error(f"Error processing {company}: {e}")
                print(f"\n⚠  Error processing {company}")
                handle_error(e)

    except Exception as e:
        logger.error(f"Geography Mode failed: {e}")
        handle_error(e)


# ===============================
# Main Menu
# ===============================

def main():

    os.makedirs("reports", exist_ok=True)

    print("\n===================================")
    print("     Account Intelligence Radar")
    print("===================================\n")
    print("Select mode:")
    print("  1) Company Mode")
    print("  2) Geography Mode")

    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == "1":
        run_company_mode()
    elif choice == "2":
        run_geography_mode()
    else:
        print("\nInvalid choice. Please enter 1 or 2.")


if __name__ == "__main__":
    main()
