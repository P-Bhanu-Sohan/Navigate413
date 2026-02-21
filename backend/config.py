import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_EMBEDDING_MODEL = "text-embedding-004"

# MongoDB Atlas
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = "navigate413"

# DigitalOcean Spaces
DO_SPACES_KEY = os.getenv("DO_SPACES_KEY")
DO_SPACES_SECRET = os.getenv("DO_SPACES_SECRET")
DO_SPACES_REGION = os.getenv("DO_SPACES_REGION", "nyc3")
DO_SPACES_BUCKET = os.getenv("DO_SPACES_BUCKET", "navigate413")
DO_SPACES_ENDPOINT = f"https://{DO_SPACES_REGION}.digitaloceanspaces.com"

# App config
TEMP_FILE_DIR = "/tmp/navigate413"
FILE_RETENTION_HOURS = 24
MAX_FILE_SIZE_MB = 50

# Ensure temp directory exists
os.makedirs(TEMP_FILE_DIR, exist_ok=True)
