"""
AI Vision Analyzer using Google Gemini for screenshot analysis.
Implements vision-based decision making for the agent.
"""
import base64
import io
import time
from typing import Dict, List, Any, Optional
from PIL import Image
import google.generativeai as genai
import structlog

from config import Config
from gemini_helper import (
    setup_gemini,
    get_generation_config,
    get_safety_settings,
    create_vision_prompt,
    parse_gemini_json,
    validate_action,
    GEMINI_FLASH,
    GEMINI_PRO,
    GEMINI_FLASH_1_5
)
from amazon_selectors import is_amazon_url, detect_amazon_page_type

logger = structlog.get_logger()


class VisionAnalyzer:
    """Analyzes screenshots using Gemini vision models to determine next actions"""
    
    def __init__(self, model_name: str = GEMINI_FLASH_1_5):
        """
        Initialize vision analyzer
        
        Args:
            model_name: Gemini model to use (default: gemini-1.5-flash)
        """
        self.model_name = model_name
        self.model = None
        self._setup()
    
    def _setup(self) -> None:
        """Setup Gemini API and initialize model"""
        try:
            setup_gemini()
            
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=get_generation_config(
                    temperature=0.4,
                    response_json=True,
                    max_tokens=2048
                ),
                safety_settings=get_safety_settings()
            )
            
            logger.info("Vision analyzer initialized", model=self.model_name)
            
        except Exception as e:
            logger.error("Failed to initialize vision analyzer", error=str(e))
            raise
    
    def _base64_to_image(self, screenshot_base64: str) -> Image.Image:
        """
        Convert base64 string to PIL Image
        
        Args:
            screenshot_base64: Base64 encoded image string
        
        Returns:
            PIL Image object
        """
        try:
            # Decode base64
            image_data = base64.b64decode(screenshot_base64)
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Ensure RGB format
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Optimize size for Gemini (max 1024x1024 for best performance)
            max_size = 1024
            if image.width > max_size or image.height > max_size:
                ratio = min(max_size / image.width, max_size / image.height)
                new_size = (int(image.width * ratio), int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.debug("Image resized for optimization", 
                           original=(image.width, image.height),
                           new=new_size)
            
            return image
            
        except Exception as e:
            logger.error("Failed to convert base64 to image", error=str(e))
            raise
    
    async def analyze_page(
        self,
        screenshot_base64: str,
        markers_map: Dict[int, Dict],
        user_goal: str,
        action_history: List[Dict] = None,
        current_url: str = ""
    ) -> Dict[str, Any]:
        """
        Analyze page screenshot and determine next action
        
        Args:
            screenshot_base64: Base64 encoded screenshot
            markers_map: Mapping of marker numbers to elements
            user_goal: User's stated goal
            action_history: List of previous actions
            current_url: Current page URL for context
        
        Returns:
            Action dictionary with keys: action, target, value, reasoning
        """
        action_history = action_history or []
        
        try:
            # Detect page context
            page_context = ""
            if current_url:
                if is_amazon_url(current_url):
                    page_type = detect_amazon_page_type(current_url)
                    page_context = f"Amazon {page_type} page"
                    logger.info("Detected Amazon page", page_type=page_type)
            
            logger.info("Analyzing page", 
                       goal=user_goal,
                       markers_count=len(markers_map),
                       history_length=len(action_history),
                       page_context=page_context)
            
            # Convert screenshot to PIL Image
            image = self._base64_to_image(screenshot_base64)
            
            # Create prompt with page context
            prompt = create_vision_prompt(markers_map, user_goal, action_history, page_context)
            
            # Retry logic with exponential backoff
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Generate response
                    logger.debug(f"Sending request to Gemini (attempt {attempt + 1})")
                    
                    response = await self._generate_with_retry(prompt, image)
                    
                    # Parse JSON response
                    action = parse_gemini_json(response.text)
                    
                    # Validate action
                    if not validate_action(action):
                        raise ValueError("Invalid action structure")
                    
                    logger.info("Vision analysis complete",
                               action=action.get('action'),
                               target=action.get('target'),
                               reasoning=action.get('reasoning')[:100])
                    
                    return action
                    
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed", error=str(e))
                    
                    if attempt < max_retries - 1:
                        # Exponential backoff
                        wait_time = 2 ** attempt
                        logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        raise
            
            # If all retries failed
            raise Exception("All retry attempts failed")
            
        except Exception as e:
            logger.error("Vision analysis failed", error=str(e))
            
            # Return safe fallback action
            return {
                "action": "done",
                "target": None,
                "value": None,
                "reasoning": f"Error during analysis: {str(e)}"
            }
    
    async def _generate_with_retry(self, prompt: str, image: Image.Image) -> Any:
        """
        Generate content with Gemini, handling rate limits
        
        Args:
            prompt: Text prompt
            image: PIL Image
        
        Returns:
            Gemini response object
        """
        try:
            # Use asyncio to make synchronous call non-blocking
            import asyncio
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                [prompt, image]
            )
            
            return response
            
        except Exception as e:
            error_str = str(e)
            
            # Handle specific Gemini errors
            if "ResourceExhausted" in error_str or "429" in error_str:
                logger.warning("Rate limit hit, waiting before retry")
                time.sleep(5)
                raise
            
            elif "InvalidArgument" in error_str:
                logger.error("Invalid argument (possibly image format issue)")
                # Try with smaller image
                smaller_image = image.resize(
                    (image.width // 2, image.height // 2),
                    Image.Resampling.LANCZOS
                )
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    [prompt, smaller_image]
                )
                return response
            
            else:
                raise
    
    async def detect_checkout_page(
        self,
        screenshot_base64: str
    ) -> Dict[str, Any]:
        """
        Detect if current page is a checkout/purchase page
        
        Args:
            screenshot_base64: Base64 encoded screenshot
        
        Returns:
            Dictionary with is_checkout, confidence, and details
        """
        try:
            logger.info("Detecting checkout page")
            
            # Convert screenshot
            image = self._base64_to_image(screenshot_base64)
            
            # Create checkout detection prompt
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
            
            # Generate response
            import asyncio
            response = await asyncio.to_thread(
                self.model.generate_content,
                [prompt, image]
            )
            
            # Parse result
            result = parse_gemini_json(response.text)
            
            logger.info("Checkout detection complete",
                       is_checkout=result.get('is_checkout'),
                       confidence=result.get('confidence'))
            
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
    
    async def extract_product_info(
        self,
        screenshot_base64: str
    ) -> Dict[str, Any]:
        """
        Extract product information from a product page
        
        Args:
            screenshot_base64: Base64 encoded screenshot
        
        Returns:
            Dictionary with product details
        """
        try:
            logger.info("Extracting product information")
            
            image = self._base64_to_image(screenshot_base64)
            
            prompt = """Analyze this product page and extract key information.

Return ONLY valid JSON:
{
  "product_name": "product title",
  "price": "price string",
  "rating": "rating if visible" | null,
  "availability": "in stock/out of stock" | null,
  "description": "brief description" | null,
  "image_url": "main product image if identifiable" | null
}

Extract only what you can clearly see in the screenshot.
"""
            
            import asyncio
            response = await asyncio.to_thread(
                self.model.generate_content,
                [prompt, image]
            )
            
            result = parse_gemini_json(response.text)
            
            logger.info("Product info extracted",
                       name=result.get('product_name'),
                       price=result.get('price'))
            
            return result
            
        except Exception as e:
            logger.error("Product extraction failed", error=str(e))
            return {
                "product_name": None,
                "price": None,
                "error": str(e)
            }


# Singleton instance
_vision_analyzer: Optional[VisionAnalyzer] = None


def get_vision_analyzer(model_name: str = GEMINI_FLASH) -> VisionAnalyzer:
    """
    Get or create vision analyzer singleton
    
    Args:
        model_name: Gemini model to use
    
    Returns:
        VisionAnalyzer instance
    """
    global _vision_analyzer
    
    if _vision_analyzer is None:
        _vision_analyzer = VisionAnalyzer(model_name=model_name)
    
    return _vision_analyzer

