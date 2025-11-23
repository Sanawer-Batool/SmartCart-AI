"""
Browser Controller using Playwright for web automation.
Provides high-level interface for browser navigation, screenshots, and interactions.
"""
import asyncio
import sys
import base64
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import structlog
from config import Config
from amazon_selectors import is_amazon_url

# CRITICAL FIX: Set event loop policy for Windows before ANY async operations
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

logger = structlog.get_logger()


class BrowserController:
    """Manages browser lifecycle and provides automation methods"""
    
    def __init__(self, headless: bool = True, use_persistent_context: bool = False):
        """
        Initialize browser controller
        
        Args:
            headless: Run browser in headless mode
            use_persistent_context: Use saved browser context with cookies/auth
        """
        self.headless = headless
        self.use_persistent_context = use_persistent_context
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Launch browser and create context"""
        if self._initialized:
            logger.warning("Browser already initialized")
            return
        
        # CRITICAL: Force set event loop policy RIGHT BEFORE browser launch
        if sys.platform == 'win32':
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            except Exception:
                pass
        
        try:
            logger.info("Launching browser", headless=self.headless)
            self.playwright = await async_playwright().start()
            
            # Launch Chromium browser
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            # Create browser context
            context_options = {
                'viewport': {'width': 1280, 'height': 720},
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'java_script_enabled': True,
            }
            
            if self.use_persistent_context:
                # Load saved context if available
                storage_path = f"{Config.BROWSER_CONTEXTS_DIR}/default_state.json"
                try:
                    context_options['storage_state'] = storage_path
                    logger.info("Loading persistent context", path=storage_path)
                except Exception as e:
                    logger.warning("Could not load persistent context", error=str(e))
            
            self.context = await self.browser.new_context(**context_options)
            
            # Create a new page
            self.page = await self.context.new_page()
            
            # Set default timeout
            self.page.set_default_timeout(Config.BROWSER_TIMEOUT)
            
            self._initialized = True
            logger.info("Browser initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize browser", error=str(e))
            await self.close()
            raise
    
    async def navigate(self, url: str, wait_until: str = None) -> Dict[str, Any]:
        """
        Navigate to a URL
        
        Args:
            url: Target URL
            wait_until: When to consider navigation complete
                       Options: 'load', 'domcontentloaded', 'networkidle'
                       If None, auto-detects based on URL (Amazon uses 'domcontentloaded')
        
        Returns:
            Dict with status and URL info
        """
        if not self._initialized or not self.page:
            raise RuntimeError("Browser not initialized. Call initialize() first.")
        
        try:
            # Auto-detect wait strategy for Amazon (never reaches networkidle)
            if wait_until is None:
                if is_amazon_url(url):
                    wait_until = "domcontentloaded"  # Amazon has continuous network activity
                    timeout = 60000  # 60 seconds for Amazon
                    logger.info("Using Amazon-optimized navigation strategy", url=url)
                else:
                    wait_until = "networkidle"
                    timeout = Config.BROWSER_TIMEOUT
            else:
                timeout = Config.BROWSER_TIMEOUT
            
            # Normalize Amazon URLs (add www if missing)
            normalized_url = url
            if is_amazon_url(url) and "www." not in url.lower():
                # Handle both http:// and https://
                if "https://amazon.com" in url.lower():
                    normalized_url = url.replace("amazon.com", "www.amazon.com")
                elif "http://amazon.com" in url.lower():
                    normalized_url = url.replace("amazon.com", "www.amazon.com")
                logger.info("Normalized Amazon URL", original=url, normalized=normalized_url)
            
            logger.info("Navigating to URL", url=normalized_url, wait_until=wait_until, timeout=timeout)
            
            # Navigate to URL with appropriate timeout
            response = await self.page.goto(normalized_url, wait_until=wait_until, timeout=timeout)
            
            # Wait a bit for dynamic content (longer for Amazon)
            wait_time = 2 if is_amazon_url(url) else 1
            await asyncio.sleep(wait_time)
            
            current_url = self.page.url
            title = await self.page.title()
            
            logger.info("Navigation complete", 
                       url=current_url, 
                       title=title,
                       status=response.status if response else None)
            
            return {
                "status": "success",
                "url": current_url,
                "title": title,
                "status_code": response.status if response else None
            }
            
        except Exception as e:
            logger.error("Navigation failed", url=url, error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "url": url
            }
    
    async def take_screenshot(self, full_page: bool = False) -> str:
        """
        Take a screenshot of the current page
        
        Args:
            full_page: Capture full scrollable page (default: visible viewport only)
        
        Returns:
            Base64 encoded screenshot string
        """
        if not self._initialized or not self.page:
            raise RuntimeError("Browser not initialized. Call initialize() first.")
        
        try:
            logger.debug("Taking screenshot", full_page=full_page)
            
            # Take screenshot as bytes
            screenshot_bytes = await self.page.screenshot(
                full_page=full_page,
                type='png'
            )
            
            # Encode to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            logger.debug("Screenshot captured", 
                        size_bytes=len(screenshot_bytes))
            
            return screenshot_base64
            
        except Exception as e:
            logger.error("Screenshot failed", error=str(e))
            raise
    
    async def click(self, selector: str, timeout: Optional[int] = None) -> bool:
        """
        Click an element by selector
        
        Args:
            selector: CSS selector for element
            timeout: Optional timeout in milliseconds
        
        Returns:
            True if successful
        """
        if not self._initialized or not self.page:
            raise RuntimeError("Browser not initialized")
        
        try:
            logger.info("Clicking element", selector=selector)
            await self.page.click(selector, timeout=timeout or Config.BROWSER_TIMEOUT)
            await asyncio.sleep(0.5)  # Wait for page response
            return True
        except Exception as e:
            logger.error("Click failed", selector=selector, error=str(e))
            return False
    
    async def fill(self, selector: str, text: str, timeout: Optional[int] = None) -> bool:
        """
        Fill an input field with text
        
        Args:
            selector: CSS selector for input element
            text: Text to fill
            timeout: Optional timeout in milliseconds
        
        Returns:
            True if successful
        """
        if not self._initialized or not self.page:
            raise RuntimeError("Browser not initialized")
        
        try:
            logger.info("Filling field", selector=selector, text_length=len(text))
            await self.page.fill(selector, text, timeout=timeout or Config.BROWSER_TIMEOUT)
            return True
        except Exception as e:
            logger.error("Fill failed", selector=selector, error=str(e))
            return False
    
    async def type_text(self, selector: str, text: str, delay: int = 100) -> bool:
        """
        Type text character by character (simulates human typing)
        
        Args:
            selector: CSS selector for input element
            text: Text to type
            delay: Delay between keystrokes in milliseconds
        
        Returns:
            True if successful
        """
        if not self._initialized or not self.page:
            raise RuntimeError("Browser not initialized")
        
        try:
            logger.info("Typing text", selector=selector, text_length=len(text))
            await self.page.type(selector, text, delay=delay)
            return True
        except Exception as e:
            logger.error("Type failed", selector=selector, error=str(e))
            return False
    
    async def scroll(self, direction: str = "down", amount: int = 500) -> bool:
        """
        Scroll the page
        
        Args:
            direction: 'down' or 'up'
            amount: Pixels to scroll
        
        Returns:
            True if successful
        """
        if not self._initialized or not self.page:
            raise RuntimeError("Browser not initialized")
        
        try:
            scroll_amount = amount if direction == "down" else -amount
            await self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await asyncio.sleep(0.5)
            return True
        except Exception as e:
            logger.error("Scroll failed", error=str(e))
            return False
    
    async def get_url(self) -> str:
        """Get current page URL"""
        if not self._initialized or not self.page:
            return ""
        return self.page.url
    
    async def get_title(self) -> str:
        """Get current page title"""
        if not self._initialized or not self.page:
            return ""
        return await self.page.title()
    
    async def save_context(self, name: str = "default") -> None:
        """
        Save browser context (cookies, localStorage, etc.)
        
        Args:
            name: Context name for the saved state file
        """
        if not self.context:
            logger.warning("No context to save")
            return
        
        try:
            storage_path = f"{Config.BROWSER_CONTEXTS_DIR}/{name}_state.json"
            await self.context.storage_state(path=storage_path)
            logger.info("Context saved", path=storage_path)
        except Exception as e:
            logger.error("Failed to save context", error=str(e))
    
    async def close(self) -> None:
        """Close browser and cleanup resources"""
        logger.info("Closing browser")
        
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error("Error during cleanup", error=str(e))
        finally:
            self._initialized = False
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None
    
    async def __aenter__(self):
        """Context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()

