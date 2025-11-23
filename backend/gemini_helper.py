"""
Google Gemini API helper utilities.
Provides functions for API setup, prompt creation, and response parsing.
"""
import os
import json
import re
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import structlog

from config import Config

logger = structlog.get_logger()

# Model names
GEMINI_FLASH = "gemini-2.0-flash-exp"
GEMINI_PRO = "gemini-1.5-pro"
GEMINI_FLASH_1_5 = "gemini-1.5-flash"


def setup_gemini() -> None:
    """
    Configure Gemini API with key from environment
    
    Raises:
        ValueError: If API key is not configured
    """
    api_key = Config.get_gemini_key()
    genai.configure(api_key=api_key)
    logger.info("Gemini API configured successfully")


def get_generation_config(
    temperature: float = 0.4,
    response_json: bool = False,
    max_tokens: int = 2048
) -> Dict[str, Any]:
    """
    Get standard generation configuration for Gemini
    
    Args:
        temperature: Sampling temperature (0.0 to 1.0)
        response_json: Whether to request JSON response format
        max_tokens: Maximum output tokens
    
    Returns:
        Generation config dictionary
    """
    config = {
        "temperature": temperature,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": max_tokens,
    }
    
    if response_json:
        config["response_mime_type"] = "application/json"
    
    return config


def get_safety_settings() -> Dict[HarmCategory, HarmBlockThreshold]:
    """
    Get safety settings for Gemini API
    
    Returns:
        Safety settings dictionary
    """
    return {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }


def create_vision_prompt(
    markers_map: Dict[int, Dict],
    user_goal: str,
    action_history: List[Dict] = None,
    page_context: str = ""
) -> str:
    """
    Create comprehensive prompt for vision analysis
    
    Args:
        markers_map: Mapping of marker numbers to element info
        user_goal: User's stated goal/objective
        action_history: List of previous actions taken
        page_context: Optional context about the current page (e.g., "Amazon homepage")
    
    Returns:
        Formatted prompt string
    """
    action_history = action_history or []
    
    # Format action history
    history_str = "None (this is the first action)"
    if action_history:
        recent_actions = action_history[-3:]  # Last 3 actions
        history_lines = []
        for i, action in enumerate(recent_actions, 1):
            action_type = action.get('action', 'unknown')
            target = action.get('target', 'N/A')
            value = action.get('value', '')
            history_lines.append(f"  {i}. {action_type} on element [{target}]" + 
                               (f" with value: {value}" if value else ""))
        history_str = '\n'.join(history_lines)
    
    # Format markers
    markers_str = ""
    for number, info in sorted(markers_map.items()):
        element_type = info.get('type', 'unknown')
        text = info.get('text', '')[:60]
        aria = info.get('aria_label', '')
        placeholder = info.get('placeholder', '')
        
        desc = f"[{number}] {element_type.upper()}"
        if text:
            desc += f' - "{text}"'
        elif aria:
            desc += f' - (aria: "{aria}")'
        elif placeholder:
            desc += f' - (placeholder: "{placeholder}")'
        
        markers_str += desc + '\n'
    
    # Add page context if available
    context_note = ""
    if page_context:
        context_note = f"\nPAGE CONTEXT: {page_context}\n"
    
    prompt = f"""You are a web automation assistant analyzing a screenshot with numbered interactive elements (red numbered labels).

USER GOAL: {user_goal}
{context_note}
AVAILABLE INTERACTIVE ELEMENTS:
{markers_str}

PREVIOUS ACTIONS:
{history_str}

Analyze the screenshot and determine the NEXT BEST ACTION to achieve the user's goal.

RULES:
1. If the goal is complete or you see a success message, use action: "done"
2. For search boxes/input fields, use action: "type" with the search query
3. For buttons, links, or clickable elements, use action: "click"
4. For scrolling to see more content, use action: "scroll"
5. AVOID repeating recent actions - check the action history
6. Choose the most relevant numbered element based on its text/label
7. Be smart: if you just typed in a search box, next action should be clicking the search button
8. IMPORTANT: Look carefully at the red numbered labels in the screenshot - use those exact numbers!

Return ONLY valid JSON with this EXACT structure:
{{
  "action": "click" | "type" | "scroll" | "done",
  "target": <marker_number>,
  "value": "<text_to_type>" | null,
  "reasoning": "<brief explanation of why this action>"
}}

ACTION TYPES:
- "click": Click on element at target marker number
- "type": Type value into input field at target marker number
- "scroll": Scroll down to see more content (target can be null)
- "done": Goal is complete (target can be null)

Remember: You must reference element numbers from the screenshot's red labels!
"""
    
    return prompt


def parse_gemini_json(response_text: str) -> Dict[str, Any]:
    """
    Parse JSON response from Gemini, handling edge cases
    
    Args:
        response_text: Raw response text from Gemini
    
    Returns:
        Parsed JSON dictionary
    
    Raises:
        ValueError: If response cannot be parsed as valid JSON
    """
    try:
        # Try direct JSON parse first
        result = json.loads(response_text)
        return result
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group(1))
            return result
        except json.JSONDecodeError:
            pass
    
    # Try to find any JSON object in the response
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group(0))
            return result
        except json.JSONDecodeError:
            pass
    
    logger.error("Could not parse JSON from response", response=response_text[:200])
    raise ValueError(f"Could not parse valid JSON from response: {response_text[:200]}")


def validate_action(action: Dict[str, Any]) -> bool:
    """
    Validate that an action dictionary has required fields
    
    Args:
        action: Action dictionary to validate
    
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['action', 'reasoning']
    
    if not all(field in action for field in required_fields):
        logger.error("Action missing required fields", action=action)
        return False
    
    valid_actions = ['click', 'type', 'scroll', 'done']
    if action['action'] not in valid_actions:
        logger.error("Invalid action type", action_type=action['action'])
        return False
    
    # Type action requires value
    if action['action'] == 'type' and not action.get('value'):
        logger.error("Type action missing value")
        return False
    
    # Click action requires target
    if action['action'] == 'click' and not action.get('target'):
        logger.error("Click action missing target")
        return False
    
    return True


def format_action_for_log(action: Dict[str, Any]) -> str:
    """
    Format an action dictionary into a readable log message
    
    Args:
        action: Action dictionary
    
    Returns:
        Formatted string
    """
    action_type = action.get('action', 'unknown')
    target = action.get('target', 'N/A')
    value = action.get('value', '')
    reasoning = action.get('reasoning', '')
    
    msg = f"Action: {action_type.upper()}"
    
    if target:
        msg += f" on element [{target}]"
    
    if value:
        msg += f' with value: "{value}"'
    
    if reasoning:
        msg += f'\nReasoning: {reasoning}'
    
    return msg


def create_checkout_detection_prompt() -> str:
    """
    Create prompt for detecting checkout/purchase pages
    
    Returns:
        Formatted prompt string
    """
    prompt = """You are analyzing a screenshot to determine if this is a checkout or order confirmation page.

Look for these indicators:
- "Place Order", "Complete Purchase", "Confirm Order" buttons
- Payment information fields (credit card, billing address)
- Order summary with total price
- Shipping information forms
- "Review Order" or "Checkout" in the page title
- Cart total or order total displayed prominently
- Terms and conditions checkboxes near purchase button

Return ONLY valid JSON:
{
  "is_checkout": true | false,
  "confidence": 0.0 to 1.0,
  "detected_keywords": ["keyword1", "keyword2"],
  "total_price": "price string" | null,
  "reasoning": "brief explanation"
}

Be conservative: only return is_checkout=true if you're confident this is a checkout page.
"""
    
    return prompt

