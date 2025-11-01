
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent.parent.parent  
BACKEND_DIR = BASE_DIR / "backend"
APP_DIR = BACKEND_DIR / "app"
DATA_DIR = BASE_DIR / "data"

class DatabaseConfig:
    HOST = os.getenv("POSTGRES_HOST", "localhost")
    PORT = os.getenv("POSTGRES_PORT", "5432")
    NAME = os.getenv("POSTGRES_DB", "negotiaai_db")
    USER = os.getenv("POSTGRES_USER", "negotiaai_user")
    PASSWORD = os.getenv("POSTGRES_PASSWORD", "Negotiaai2025Secure")
    
    @classmethod
    def get_url(cls):
        return f"postgresql://{cls.USER}:{cls.PASSWORD}@{cls.HOST}:{cls.PORT}/{cls.NAME}"


class LLMConfig:
    PROVIDER = "Google Gemini"
    MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash-exp")
    API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))


class AppConfig:
    APP_NAME = "negotiaai"
    VERSION = "1.0.0"
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    HOST = os.getenv("APP_HOST", "0.0.0.0")
    PORT = int(os.getenv("SERVER_PORT", "5000"))
    
    COMPROVANTES_DIR = DATA_DIR / "comprovantes"
    LOGS_DIR = DATA_DIR / "logs"
    
    PROMPTS_DIR = APP_DIR / "infrastructure" / "llm" / "prompts"
    INSTRUCTIONS_FILE = PROMPTS_DIR / "instruction_agente_negociacao.txt"
    DESCRIPTIONS_FILE = PROMPTS_DIR / "description_agente_negociacao.txt"
    
    @classmethod
    def ensure_directories(cls):
        cls.COMPROVANTES_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)


class LoggingConfig:
    LEVEL = os.getenv("LOG_LEVEL", "INFO")
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


AppConfig.ensure_directories()
