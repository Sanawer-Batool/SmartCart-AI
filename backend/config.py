"""
Configuration management for the E-Commerce Agent.
Loads environment variables and provides centralized config access.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Get the directory where this config.py file is located (backend folder)
BASE_DIR = Path(__file__).resolve().parent

# Explicitly load .env file from backend directory
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Debug: Print if .env was found and loaded
if env_path.exists():
    print(f"[OK] .env file found at: {env_path}")
    print(f"[OK] API key loaded: {os.getenv('GOOGLE_API_KEY', 'NOT FOUND')[:20]}...")
else:
    print(f"[WARNING] .env file NOT found at: {env_path}")
    print(f"          Current directory: {os.getcwd()}")


class Config:
    """Application configuration class"""
    
    # Google Gemini API
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Browser settings
    HEADLESS: bool = os.getenv("HEADLESS", "True").lower() == "true"
    BROWSER_TIMEOUT: int = int(os.getenv("BROWSER_TIMEOUT", "30000"))
    
    # Agent settings
    MAX_ITERATIONS: int = 20
    
    # Directories
    BROWSER_CONTEXTS_DIR: str = "browser_contexts"
    LOGS_DIR: str = "agent_logs"
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration"""
        if not cls.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY is required. "
                "Get your key at: https://aistudio.google.com/app/apikey"
            )
    
    @classmethod
    def get_gemini_key(cls) -> str:
        """Get Gemini API key with validation"""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not configured")
        return cls.GOOGLE_API_KEY


# Create directories if they don't exist
os.makedirs(Config.BROWSER_CONTEXTS_DIR, exist_ok=True)
os.makedirs(Config.LOGS_DIR, exist_ok=True)

