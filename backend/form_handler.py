"""
Form Detection and Filling Utilities.
Helps identify and fill form fields intelligently.
"""
from typing import Dict, List, Any, Optional
from playwright.async_api import Page
import structlog

logger = structlog.get_logger()


async def detect_form_fields(
    page: Page,
    markers_map: Dict[int, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Detect and categorize form fields on the page
    
    Args:
        page: Playwright page instance
        markers_map: Mapping of marker numbers to elements
    
    Returns:
        Dictionary categorizing form fields:
        {
            "email": [marker_numbers],
            "password": [marker_numbers],
            "text": [marker_numbers],
            "search": [marker_numbers],
            "tel": [marker_numbers],
            "submit": [marker_numbers]
        }
    """
    logger.info("Detecting form fields", markers_count=len(markers_map))
    
    categorized = {
        "email": [],
        "password": [],
        "text": [],
        "search": [],
        "tel": [],
        "number": [],
        "submit": [],
        "button": []
    }
    
    for marker_num, info in markers_map.items():
        element_type = info.get('type', '').lower()
        input_type = info.get('input_type', '').lower()
        name = info.get('name', '').lower()
        aria_label = info.get('aria_label', '').lower()
        placeholder = info.get('placeholder', '').lower()
        text = info.get('text', '').lower()
        
        # Categorize by input type
        if element_type == 'input':
            if input_type == 'email' or 'email' in name or 'email' in placeholder:
                categorized['email'].append(marker_num)
            
            elif input_type == 'password' or 'password' in name:
                categorized['password'].append(marker_num)
            
            elif input_type == 'tel' or 'phone' in name or 'tel' in name:
                categorized['tel'].append(marker_num)
            
            elif input_type == 'number':
                categorized['number'].append(marker_num)
            
            elif input_type == 'search' or 'search' in name or 'search' in aria_label:
                categorized['search'].append(marker_num)
            
            elif input_type == 'submit':
                categorized['submit'].append(marker_num)
            
            else:
                categorized['text'].append(marker_num)
        
        elif element_type == 'button' or element_type == '[role="button"]':
            if 'submit' in text or 'search' in text or 'go' in text:
                categorized['submit'].append(marker_num)
            else:
                categorized['button'].append(marker_num)
    
    logger.info("Form field detection complete",
               email=len(categorized['email']),
               password=len(categorized['password']),
               search=len(categorized['search']),
               buttons=len(categorized['button']))
    
    return categorized


async def fill_form(
    page: Page,
    field_data: Dict[str, str],
    simulate_human: bool = True
) -> Dict[str, Any]:
    """
    Fill form fields with provided data
    
    Args:
        page: Playwright page instance
        field_data: Dictionary mapping field selectors to values
        simulate_human: If True, types slowly to simulate human behavior
    
    Returns:
        Dictionary with fill results:
        {
            "success": bool,
            "filled_fields": int,
            "failed_fields": List[str],
            "errors": List[str]
        }
    """
    logger.info("Filling form", fields_count=len(field_data))
    
    filled_count = 0
    failed_fields = []
    errors = []
    
    for selector, value in field_data.items():
        try:
            logger.debug("Filling field", selector=selector, value_length=len(value))
            
            # Clear existing value
            await page.fill(selector, "")
            
            if simulate_human:
                # Type with human-like delays
                await page.type(selector, value, delay=50)
            else:
                # Fill instantly
                await page.fill(selector, value)
            
            filled_count += 1
            
        except Exception as e:
            logger.error("Failed to fill field", 
                        selector=selector,
                        error=str(e))
            failed_fields.append(selector)
            errors.append(f"{selector}: {str(e)}")
    
    success = len(failed_fields) == 0
    
    result = {
        "success": success,
        "filled_fields": filled_count,
        "failed_fields": failed_fields,
        "errors": errors
    }
    
    logger.info("Form filling complete",
               success=success,
               filled=filled_count,
               failed=len(failed_fields))
    
    return result


async def find_search_box(markers_map: Dict[int, Dict[str, Any]]) -> Optional[int]:
    """
    Find the most likely search box on the page
    
    Args:
        markers_map: Mapping of marker numbers to elements
    
    Returns:
        Marker number of search box, or None if not found
    """
    search_indicators = ['search', 'query', 'q', 'find']
    
    # First pass: look for explicit search inputs
    for marker_num, info in markers_map.items():
        if info.get('type') == 'input':
            input_type = info.get('input_type', '').lower()
            name = info.get('name', '').lower()
            placeholder = info.get('placeholder', '').lower()
            aria_label = info.get('aria_label', '').lower()
            
            if input_type == 'search':
                return marker_num
            
            for indicator in search_indicators:
                if indicator in name or indicator in placeholder or indicator in aria_label:
                    return marker_num
    
    # Second pass: look for any text input near top of page
    text_inputs = [
        (num, info) for num, info in markers_map.items()
        if info.get('type') == 'input' and 
        info.get('input_type', '') in ['text', '']
    ]
    
    if text_inputs:
        # Return the topmost text input
        topmost = min(text_inputs, key=lambda x: x[1].get('position', {}).get('y', 9999))
        return topmost[0]
    
    return None


async def find_submit_button(markers_map: Dict[int, Dict[str, Any]], near_marker: Optional[int] = None) -> Optional[int]:
    """
    Find a submit button, optionally near a specific element
    
    Args:
        markers_map: Mapping of marker numbers to elements
        near_marker: Marker number to search near (optional)
    
    Returns:
        Marker number of submit button, or None if not found
    """
    submit_keywords = ['search', 'go', 'submit', 'find', 'enter']
    
    candidates = []
    
    for marker_num, info in markers_map.items():
        element_type = info.get('type', '').lower()
        text = info.get('text', '').lower()
        
        if element_type in ['button', 'input']:
            # Check if it's a submit button
            if info.get('input_type') == 'submit':
                candidates.append((marker_num, 100))  # High priority
            
            # Check text content
            for keyword in submit_keywords:
                if keyword in text:
                    candidates.append((marker_num, 50))
                    break
    
    if not candidates:
        return None
    
    # If near_marker specified, prefer buttons close to it
    if near_marker and near_marker in markers_map:
        ref_pos = markers_map[near_marker].get('position', {})
        ref_y = ref_pos.get('y', 0)
        
        # Sort by proximity to reference marker
        def distance_score(item):
            marker_num, priority = item
            pos = markers_map[marker_num].get('position', {})
            y_diff = abs(pos.get('y', 9999) - ref_y)
            return y_diff - priority
        
        candidates.sort(key=distance_score)
    else:
        # Sort by priority
        candidates.sort(key=lambda x: -x[1])
    
    return candidates[0][0] if candidates else None

