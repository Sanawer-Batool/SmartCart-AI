"""
Amazon-specific selectors for reliable element detection.
Provides stable, tested selectors for common Amazon page elements.
"""
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import structlog

logger = structlog.get_logger()


# Amazon-specific selectors with multiple fallbacks
AMAZON_SELECTORS = {
    "search_box": [
        "#twotabsearchtextbox",
        "input[name='field-keywords']",
        "input[type='text'][aria-label*='Search']",
        "input#nav-search-keywords",
        "input.nav-input",
    ],
    "search_button": [
        "#nav-search-submit-button",
        "input[type='submit'][value='Go']",
        "input.nav-input[type='submit']",
        "button[type='submit'][aria-label*='Go']",
        "#nav-search-bar-form input[type='submit']",
    ],
    "product_link": [
        "h2 a.a-link-normal",
        ".s-result-item h2 a",
        "div[data-component-type='s-search-result'] h2 a",
        "a.s-no-outline",
        ".s-product-image-container a",
    ],
    "add_to_cart": [
        "#add-to-cart-button",
        "input#add-to-cart-button",
        "button[name='submit.add-to-cart']",
        "#submit.add-to-cart-announce",
    ],
    "buy_now": [
        "#buy-now-button",
        "input#buy-now-button",
        "button[name='submit.buy-now']",
    ],
    "price": [
        ".a-price-whole",
        "span.a-price",
        ".a-offscreen",
        "#priceblock_ourprice",
        "#priceblock_dealprice",
    ],
    "next_page": [
        ".s-pagination-next",
        "a:contains('Next')",
        "li.a-last a",
    ],
    "filter_options": [
        "#s-refinements a",
        ".a-checkbox",
        "li.a-spacing-micro a",
    ],
}


def is_amazon_url(url: str) -> bool:
    """
    Check if URL is an Amazon domain
    
    Args:
        url: URL to check
    
    Returns:
        True if Amazon domain
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Check for amazon domains (including international)
        amazon_domains = [
            'amazon.com',
            'amazon.co.uk',
            'amazon.ca',
            'amazon.de',
            'amazon.fr',
            'amazon.it',
            'amazon.es',
            'amazon.in',
            'amazon.co.jp',
            'amazon.com.au',
            'amazon.com.mx',
            'amazon.com.br',
        ]
        
        # Check if any Amazon domain is in the URL
        is_amazon = any(domain.endswith(d) or domain == d for d in amazon_domains)
        
        logger.debug("Amazon URL check", url=url, is_amazon=is_amazon)
        
        return is_amazon
        
    except Exception as e:
        logger.error("Error checking Amazon URL", url=url, error=str(e))
        return False


def detect_amazon_page_type(url: str) -> str:
    """
    Detect the type of Amazon page
    
    Args:
        url: Current page URL
    
    Returns:
        Page type: 'home', 'search', 'product', 'cart', 'checkout', 'unknown'
    """
    url_lower = url.lower()
    
    if '/gp/cart/' in url_lower or '/cart' in url_lower:
        return 'cart'
    elif '/gp/buy/' in url_lower or '/checkout' in url_lower or '/ap/signin' in url_lower:
        return 'checkout'
    elif '/dp/' in url_lower or '/gp/product/' in url_lower:
        return 'product'
    elif '/s?' in url_lower or 'field-keywords=' in url_lower:
        return 'search'
    elif url_lower.endswith('amazon.com') or url_lower.endswith('amazon.com/'):
        return 'home'
    else:
        return 'unknown'


def get_amazon_element_selectors(element_type: str) -> List[str]:
    """
    Get Amazon-specific selectors for an element type
    
    Args:
        element_type: Type of element (e.g., 'search_box', 'search_button')
    
    Returns:
        List of CSS selectors to try, in order of preference
    """
    return AMAZON_SELECTORS.get(element_type, [])


def build_xpath_selector(element_info: Dict[str, Any]) -> Optional[str]:
    """
    Build an XPath selector for an element (more stable than CSS classes)
    
    Args:
        element_info: Element information dict
    
    Returns:
        XPath selector string or None
    """
    try:
        element_type = element_info.get('type', '').lower()
        text = element_info.get('text', '').strip()
        aria_label = element_info.get('aria_label', '').strip()
        placeholder = element_info.get('placeholder', '').strip()
        
        # Build XPath based on available attributes
        xpath_parts = []
        
        # Start with element type
        xpath = f"//{element_type}"
        
        # Add text matching if available (partial match)
        if text and len(text) < 50:
            xpath_parts.append(f"contains(text(), '{text[:30]}')")
        
        # Add aria-label matching
        if aria_label:
            xpath_parts.append(f"@aria-label='{aria_label}'")
        
        # Add placeholder matching
        if placeholder:
            xpath_parts.append(f"@placeholder='{placeholder}'")
        
        # Add name attribute if available
        if element_info.get('name'):
            xpath_parts.append(f"@name='{element_info['name']}'")
        
        # Combine xpath parts
        if xpath_parts:
            xpath += "[" + " or ".join(xpath_parts) + "]"
            return xpath
        
        return None
        
    except Exception as e:
        logger.error("Error building XPath", error=str(e))
        return None


def enhance_element_with_amazon_selectors(
    element_info: Dict[str, Any],
    page_url: str
) -> Dict[str, Any]:
    """
    Enhance element info with Amazon-specific selectors
    
    Args:
        element_info: Original element information
        page_url: Current page URL
    
    Returns:
        Enhanced element info with multiple selectors
    """
    if not is_amazon_url(page_url):
        return element_info
    
    enhanced = element_info.copy()
    selectors = [enhanced.get('selector', '')]
    
    # Determine element purpose based on its attributes
    element_type = enhanced.get('type', '').lower()
    text = enhanced.get('text', '').lower()
    aria_label = enhanced.get('aria_label', '').lower()
    placeholder = enhanced.get('placeholder', '').lower()
    name = enhanced.get('name', '').lower()
    
    # Match against Amazon element types
    if element_type == 'input':
        if 'search' in placeholder or 'search' in aria_label or 'field-keywords' in name:
            selectors = get_amazon_element_selectors('search_box') + selectors
        elif enhanced.get('input_type') == 'submit':
            if 'search' in aria_label or 'go' in text.lower():
                selectors = get_amazon_element_selectors('search_button') + selectors
    
    elif element_type == 'button':
        if 'add to cart' in text or 'add-to-cart' in enhanced.get('selector', ''):
            selectors = get_amazon_element_selectors('add_to_cart') + selectors
        elif 'buy now' in text:
            selectors = get_amazon_element_selectors('buy_now') + selectors
        elif 'search' in aria_label or 'go' in text:
            selectors = get_amazon_element_selectors('search_button') + selectors
    
    elif element_type == 'a':
        if 's-result-item' in enhanced.get('selector', ''):
            selectors = get_amazon_element_selectors('product_link') + selectors
    
    # Build XPath as additional fallback
    xpath = build_xpath_selector(enhanced)
    if xpath:
        selectors.append(xpath)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_selectors = []
    for sel in selectors:
        if sel and sel not in seen:
            seen.add(sel)
            unique_selectors.append(sel)
    
    # Store all selectors
    enhanced['selectors'] = unique_selectors
    enhanced['selector'] = unique_selectors[0] if unique_selectors else enhanced.get('selector', '')
    
    return enhanced


def get_amazon_search_workflow_selectors() -> Dict[str, List[str]]:
    """
    Get selectors for common Amazon search workflow
    
    Returns:
        Dict of workflow step -> list of selectors
    """
    return {
        "search_input": get_amazon_element_selectors('search_box'),
        "search_submit": get_amazon_element_selectors('search_button'),
        "product_links": get_amazon_element_selectors('product_link'),
        "add_to_cart": get_amazon_element_selectors('add_to_cart'),
    }

