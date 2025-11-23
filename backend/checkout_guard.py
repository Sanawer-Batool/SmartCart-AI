"""
Checkout Detection and Safety Guards.
Prevents accidental purchases by requiring human approval.
"""
import time
from typing import Dict, Any, Optional
from playwright.async_api import Page
import structlog

from ai_vision import get_vision_analyzer
from gemini_helper import create_checkout_detection_prompt

logger = structlog.get_logger()


# Cache for checkout detection results
_detection_cache: Dict[str, tuple[Dict[str, Any], float]] = {}
CACHE_TTL = 5.0  # seconds


async def is_checkout_page(
    page: Page,
    screenshot_base64: str
) -> Dict[str, Any]:
    """
    Detect if current page is a checkout/order confirmation page
    
    Uses Gemini vision to analyze the page and look for checkout indicators.
    Results are cached for a few seconds to avoid duplicate API calls.
    
    Args:
        page: Playwright page instance
        screenshot_base64: Base64 encoded screenshot
    
    Returns:
        Dictionary with detection results:
        {
            "is_checkout": bool,
            "confidence": float (0.0 to 1.0),
            "detected_keywords": List[str],
            "total_price": str or None,
            "reasoning": str
        }
    """
    try:
        # Generate cache key from URL
        url = page.url
        current_time = time.time()
        
        # Check cache
        if url in _detection_cache:
            cached_result, cached_time = _detection_cache[url]
            if current_time - cached_time < CACHE_TTL:
                logger.debug("Using cached checkout detection", url=url)
                return cached_result
        
        logger.info("Detecting checkout page", url=url)
        
        # Use vision analyzer for detection
        vision_analyzer = get_vision_analyzer()
        result = await vision_analyzer.detect_checkout_page(screenshot_base64)
        
        # Cache result
        _detection_cache[url] = (result, current_time)
        
        logger.info("Checkout detection complete",
                   is_checkout=result.get('is_checkout'),
                   confidence=result.get('confidence'),
                   url=url)
        
        return result
        
    except Exception as e:
        logger.error("Checkout detection failed", error=str(e))
        return {
            "is_checkout": False,
            "confidence": 0.0,
            "detected_keywords": [],
            "total_price": None,
            "reasoning": f"Detection failed: {str(e)}"
        }


async def check_before_click(
    page: Page,
    screenshot_base64: str,
    element_text: str = ""
) -> Dict[str, Any]:
    """
    Check if a click action is safe (not a purchase button)
    
    Args:
        page: Playwright page instance
        screenshot_base64: Current page screenshot
        element_text: Text of element about to be clicked
    
    Returns:
        Dictionary with safety check results:
        {
            "safe": bool,
            "requires_approval": bool,
            "reason": str,
            "checkout_info": dict (if checkout detected)
        }
    """
    # Check if current page is a checkout page
    detection = await is_checkout_page(page, screenshot_base64)
    
    # High-risk keywords in element text
    high_risk_keywords = [
        'place order',
        'complete purchase',
        'confirm order',
        'buy now',
        'complete order',
        'submit order',
        'pay now',
        'confirm purchase',
        'checkout',
        'confirm payment'
    ]
    
    element_text_lower = element_text.lower()
    is_risky_element = any(keyword in element_text_lower for keyword in high_risk_keywords)
    
    # Determine if approval is required
    requires_approval = False
    reason = "Safe to proceed"
    
    if detection.get('is_checkout', False) and detection.get('confidence', 0) > 0.7:
        if is_risky_element:
            requires_approval = True
            reason = f"Checkout page detected with purchase button: '{element_text}'"
        else:
            # On checkout page but not clicking purchase button
            reason = "On checkout page but element appears safe"
    
    elif is_risky_element:
        # Not detected as checkout but element text is risky
        requires_approval = True
        reason = f"Potentially risky action: clicking '{element_text}'"
    
    result = {
        "safe": not requires_approval,
        "requires_approval": requires_approval,
        "reason": reason,
        "checkout_info": detection if detection.get('is_checkout') else None
    }
    
    logger.info("Safety check complete",
               safe=result["safe"],
               requires_approval=requires_approval,
               element_text=element_text[:50])
    
    return result


def clear_detection_cache() -> None:
    """Clear the checkout detection cache"""
    global _detection_cache
    _detection_cache.clear()
    logger.debug("Detection cache cleared")


def extract_order_summary(checkout_info: Dict[str, Any]) -> str:
    """
    Format checkout information into a readable summary
    
    Args:
        checkout_info: Checkout detection result
    
    Returns:
        Formatted summary string
    """
    lines = ["=== ORDER CONFIRMATION REQUIRED ==="]
    
    if checkout_info.get('total_price'):
        lines.append(f"Total Price: {checkout_info['total_price']}")
    
    if checkout_info.get('detected_keywords'):
        lines.append(f"Detected: {', '.join(checkout_info['detected_keywords'])}")
    
    lines.append(f"\nConfidence: {checkout_info.get('confidence', 0):.0%}")
    
    if checkout_info.get('reasoning'):
        lines.append(f"Reason: {checkout_info['reasoning']}")
    
    lines.append("\n⚠️  This action will complete a purchase!")
    lines.append("Please review and approve to continue.")
    
    return "\n".join(lines)

