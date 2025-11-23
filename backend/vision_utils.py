"""
Vision utilities for Set-of-Marks marker injection.
Injects numbered labels on interactive elements for AI vision analysis.
"""
from typing import Dict, List, Any, Optional
from playwright.async_api import Page
import structlog
from amazon_selectors import (
    is_amazon_url,
    detect_amazon_page_type,
    enhance_element_with_amazon_selectors
)

logger = structlog.get_logger()


async def inject_markers(page: Page) -> Dict[int, Dict[str, Any]]:
    """
    Inject numbered markers on all interactive elements
    
    This implements the "Set-of-Marks" visual prompting technique where
    interactive elements are labeled with numbers that the AI can reference.
    
    Args:
        page: Playwright page instance
    
    Returns:
        Dictionary mapping marker numbers to element information:
        {
            1: {
                "type": "button",
                "text": "Add to Cart",
                "selector": "#add-to-cart-btn",
                "selectors": ["#add-to-cart-btn", "button.add-cart"],
                "aria_label": "Add to cart",
                "position": {"x": 100, "y": 200}
            },
            ...
        }
    """
    # Get current URL to check if it's Amazon
    current_url = page.url
    is_amazon = is_amazon_url(current_url)
    
    logger.info("Injecting markers on page", url=current_url, is_amazon=is_amazon)
    
    # JavaScript to inject markers and extract element information
    markers_script = """
    () => {
        // Remove existing markers if any
        document.querySelectorAll('.ai-marker-label').forEach(el => el.remove());
        
        const markers = {};
        let markerNumber = 1;
        
        // Find all interactive elements
        const selectors = [
            'a[href]',
            'button',
            'input:not([type="hidden"])',
            'select',
            'textarea',
            '[role="button"]',
            '[role="link"]',
            '[role="textbox"]',
            '[onclick]',
            '.btn',
            '.button'
        ];
        
        const elements = document.querySelectorAll(selectors.join(', '));
        const processedElements = new Set();
        
        elements.forEach(element => {
            // Skip if already processed or not visible
            if (processedElements.has(element)) return;
            
            const rect = element.getBoundingClientRect();
            const isVisible = (
                rect.width > 0 &&
                rect.height > 0 &&
                rect.top < window.innerHeight &&
                rect.bottom > 0 &&
                rect.left < window.innerWidth &&
                rect.right > 0 &&
                window.getComputedStyle(element).visibility !== 'hidden' &&
                window.getComputedStyle(element).display !== 'none'
            );
            
            if (!isVisible) return;
            
            processedElements.add(element);
            
            // Create marker label
            const label = document.createElement('div');
            label.className = 'ai-marker-label';
            label.textContent = markerNumber;
            label.style.cssText = `
                position: absolute;
                background: rgba(255, 0, 0, 0.8);
                color: white;
                font-weight: bold;
                font-size: 12px;
                padding: 2px 6px;
                border-radius: 3px;
                z-index: 999999;
                pointer-events: none;
                font-family: Arial, sans-serif;
                line-height: 1;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                border: 1px solid rgba(255, 255, 255, 0.3);
            `;
            
            // Position at top-left of element
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
            
            label.style.top = (rect.top + scrollTop) + 'px';
            label.style.left = (rect.left + scrollLeft) + 'px';
            
            document.body.appendChild(label);
            
            // Generate multiple selectors for robustness
            const selectors = [];
            
            // Priority 1: ID selector (most stable)
            if (element.id) {
                selectors.push('#' + element.id);
            }
            
            // Priority 2: Name attribute (common in forms)
            if (element.name) {
                selectors.push(`${element.tagName.toLowerCase()}[name="${element.name}"]`);
            }
            
            // Priority 3: Data attributes (stable)
            for (const attr of element.attributes) {
                if (attr.name.startsWith('data-')) {
                    selectors.push(`${element.tagName.toLowerCase()}[${attr.name}="${attr.value}"]`);
                    break; // Just use the first data attribute
                }
            }
            
            // Priority 4: aria-label (stable and semantic)
            if (element.getAttribute('aria-label')) {
                selectors.push(`${element.tagName.toLowerCase()}[aria-label="${element.getAttribute('aria-label')}"]`);
            }
            
            // Priority 5: Class-based selector (less stable but common)
            if (element.className) {
                const classes = Array.from(element.classList)
                    .filter(c => !c.startsWith('ai-marker'))
                    .slice(0, 2) // Use only first 2 classes
                    .join('.');
                if (classes) {
                    selectors.push(element.tagName.toLowerCase() + '.' + classes);
                }
            }
            
            // Priority 6: Type attribute for inputs
            if (element.type) {
                selectors.push(`${element.tagName.toLowerCase()}[type="${element.type}"]`);
            }
            
            // Priority 7: nth-child fallback
            const parent = element.parentElement;
            if (parent) {
                const index = Array.from(parent.children).indexOf(element) + 1;
                selectors.push(`${element.tagName.toLowerCase()}:nth-child(${index})`);
            }
            
            // Use the first available selector as primary
            const selector = selectors[0] || element.tagName.toLowerCase();
            
            // Extract element information
            markers[markerNumber] = {
                type: element.tagName.toLowerCase(),
                text: element.innerText?.trim().substring(0, 100) || element.value || '',
                selector: selector,
                selectors: selectors, // Store all selectors for fallback
                aria_label: element.getAttribute('aria-label') || '',
                placeholder: element.getAttribute('placeholder') || '',
                href: element.getAttribute('href') || '',
                name: element.getAttribute('name') || '',
                input_type: element.getAttribute('type') || '',
                position: {
                    x: Math.round(rect.left + scrollLeft),
                    y: Math.round(rect.top + scrollTop)
                }
            };
            
            markerNumber++;
        });
        
        return markers;
    }
    """
    
    try:
        # Execute script and get markers mapping
        markers_map = await page.evaluate(markers_script)
        
        # Enhance markers with Amazon-specific selectors if on Amazon
        if is_amazon:
            enhanced_markers = {}
            for marker_num, element_info in markers_map.items():
                enhanced_info = enhance_element_with_amazon_selectors(element_info, current_url)
                enhanced_markers[int(marker_num)] = enhanced_info
            markers_map = enhanced_markers
        
        logger.info("Markers injected successfully", count=len(markers_map), is_amazon=is_amazon)
        
        return markers_map
        
    except Exception as e:
        logger.error("Failed to inject markers", error=str(e))
        return {}


async def remove_markers(page: Page) -> None:
    """
    Remove all injected markers from the page
    
    Args:
        page: Playwright page instance
    """
    try:
        await page.evaluate("""
            () => {
                document.querySelectorAll('.ai-marker-label').forEach(el => el.remove());
            }
        """)
        logger.debug("Markers removed")
    except Exception as e:
        logger.error("Failed to remove markers", error=str(e))


async def get_element_by_marker(page: Page, markers_map: Dict[int, Dict], marker_number: int) -> Optional[str]:
    """
    Get the selector for an element by its marker number with retry logic
    
    Args:
        page: Playwright page instance
        markers_map: Mapping of marker numbers to element info
        marker_number: The marker number to look up
    
    Returns:
        CSS selector for the element, or None if not found
    """
    import asyncio
    
    if marker_number not in markers_map:
        logger.warning("Marker number not found", marker=marker_number)
        return None
    
    element_info = markers_map[marker_number]
    
    # Get all available selectors
    selectors = element_info.get("selectors", [])
    if not selectors:
        # Fallback to single selector if selectors array not available
        selectors = [element_info.get("selector")]
    
    # Remove None values
    selectors = [s for s in selectors if s]
    
    if not selectors:
        logger.warning("No selectors available for marker", marker=marker_number)
        return None
    
    logger.info("Trying selectors for marker", 
               marker=marker_number,
               selector_count=len(selectors))
    
    # Try each selector with timeout
    for i, selector in enumerate(selectors):
        try:
            logger.debug(f"Trying selector {i+1}/{len(selectors)}", selector=selector)
            
            # Wait for element to be present and visible (max 3 seconds)
            await page.wait_for_selector(selector, state="visible", timeout=3000)
            
            # Verify element is actually visible and interactable
            element = await page.query_selector(selector)
            if element:
                is_visible = await element.is_visible()
                is_enabled = await element.is_enabled()
                
                if is_visible and is_enabled:
                    logger.info("Found element with selector", 
                              marker=marker_number,
                              selector=selector,
                              attempt=i+1)
                    return selector
                else:
                    logger.debug("Element found but not interactable",
                               selector=selector,
                               visible=is_visible,
                               enabled=is_enabled)
            
        except Exception as e:
            logger.debug(f"Selector {i+1} failed", selector=selector, error=str(e))
            # Try next selector
            continue
    
    # If all selectors failed, try one more time with the first selector and force it
    logger.warning("All selectors failed, trying first selector without visibility check",
                  marker=marker_number)
    try:
        first_selector = selectors[0]
        element = await page.query_selector(first_selector)
        if element:
            logger.info("Found element without strict checks", selector=first_selector)
            return first_selector
    except Exception as e:
        logger.error("Final fallback failed", error=str(e))
    
    logger.error("Could not find element for marker", 
                marker=marker_number,
                tried_selectors=selectors)
    return None


async def highlight_element(page: Page, selector: str, duration: int = 2000) -> None:
    """
    Temporarily highlight an element on the page
    
    Args:
        page: Playwright page instance
        selector: CSS selector for element
        duration: How long to show highlight in milliseconds
    """
    highlight_script = f"""
    (selector, duration) => {{
        const element = document.querySelector(selector);
        if (!element) return;
        
        const highlight = document.createElement('div');
        highlight.style.cssText = `
            position: absolute;
            border: 3px solid #00ff00;
            background: rgba(0, 255, 0, 0.1);
            pointer-events: none;
            z-index: 999998;
            box-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
        `;
        
        const rect = element.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
        
        highlight.style.top = (rect.top + scrollTop) + 'px';
        highlight.style.left = (rect.left + scrollLeft) + 'px';
        highlight.style.width = rect.width + 'px';
        highlight.style.height = rect.height + 'px';
        
        document.body.appendChild(highlight);
        
        setTimeout(() => highlight.remove(), duration);
    }}
    """
    
    try:
        await page.evaluate(f"({highlight_script})('{selector}', {duration})")
    except Exception as e:
        logger.error("Failed to highlight element", selector=selector, error=str(e))


def format_markers_for_prompt(markers_map: Dict[int, Dict]) -> str:
    """
    Format markers map into a readable string for LLM prompt
    
    Args:
        markers_map: Mapping of marker numbers to element info
    
    Returns:
        Formatted string describing all markers
    """
    if not markers_map:
        return "No interactive elements found on the page."
    
    lines = []
    for number, info in sorted(markers_map.items()):
        element_type = info.get('type', 'unknown')
        text = info.get('text', '')[:50]  # Limit text length
        aria_label = info.get('aria_label', '')
        placeholder = info.get('placeholder', '')
        
        description_parts = [f"[{number}]", element_type.upper()]
        
        if text:
            description_parts.append(f'"{text}"')
        elif aria_label:
            description_parts.append(f'(aria: "{aria_label}")')
        elif placeholder:
            description_parts.append(f'(placeholder: "{placeholder}")')
        
        if info.get('href'):
            description_parts.append(f"→ {info['href'][:30]}")
        
        lines.append(' '.join(description_parts))
    
    return '\n'.join(lines)


