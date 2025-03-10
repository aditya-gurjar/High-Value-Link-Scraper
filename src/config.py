import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./links.db")

# API configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Crawler configuration
CRAWL_LIMIT = int(os.getenv("CRAWL_LIMIT", "50"))  # Default limit of pages to crawl
FORMATS = ["markdown", "html"]

# Link prioritization
HIGH_VALUE_KEYWORDS = [
    "acfr",
    "budget",
    "finance",
    "financial",
    "report",
    "contact",
    "director",
    "annual",
    "comprehensive",
    "statement",
    "treasurer",
    "audit",
    "department",
    "staff",
    "official",
    "government",
    "council",
    "meeting",
    "document",
    "download",
    "pdf",
    "fiscal",
    "mayor",
    "administrator",
    "clerk",
    "service"
]