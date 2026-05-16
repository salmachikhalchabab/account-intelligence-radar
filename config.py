import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SERPAPI_KEY = os.getenv("SERPAPI_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

    SERPAPI_URL = "https://serpapi.com/search"
    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    FIRECRAWL_URL = "https://api.firecrawl.dev/v1/extract"

    # Centralized model name — change once here to affect all services
    LLM_MODEL = os.getenv("LLM_MODEL")


settings = Settings()