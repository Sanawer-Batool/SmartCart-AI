"""
Startup wrapper for SmartCart AI that ensures proper Windows event loop policy
"""
import sys
import asyncio

# CRITICAL: Set Windows event loop policy BEFORE anything else
if sys.platform == 'win32':
    # Force ProactorEventLoop for subprocess support
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("[STARTUP] Windows ProactorEventLoop policy set")

# Now import and run the app
if __name__ == "__main__":
    import uvicorn
    from config import Config
    
    print(f"[STARTUP] Starting server on {Config.HOST}:{Config.PORT}")
    print(f"[STARTUP] Debug mode: {Config.DEBUG}")
    print(f"[STARTUP] Headless: {Config.HEADLESS}")
    
    uvicorn.run(
        "app:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        loop="asyncio"  # Force asyncio loop
    )


