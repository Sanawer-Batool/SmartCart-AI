"""
Start SmartCart AI backend in production mode (no reload)
This ensures the Windows event loop policy is properly set
"""
import asyncio
import sys

# CRITICAL: Set Windows event loop policy BEFORE any imports
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("[FIX] Windows ProactorEventLoop policy set")

import uvicorn
from config import Config

if __name__ == "__main__":
    print(f"Starting backend on {Config.HOST}:{Config.PORT}")
    print(f"Debug mode: {Config.DEBUG}")
    print(f"Headless browser: {Config.HEADLESS}")
    
    uvicorn.run(
        "app:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=False,  # No reload to avoid subprocess issues
        loop="asyncio",
        log_level="info"
    )

