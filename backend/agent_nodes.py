"""
LangGraph nodes for the shopping agent workflow.
Each node performs a specific step in the agent's reasoning loop.
"""
import asyncio
from typing import Dict, Any
from langchain_core.messages import AIMessage
import structlog

from agent_state import (
    AgentState,
    add_message,
    add_action,
    increment_iteration,
    set_status,
    set_error,
    get_recent_actions
)
from browser_controller import BrowserController
from vision_utils import inject_markers, remove_markers, get_element_by_marker
from ai_vision import get_vision_analyzer
from checkout_guard import check_before_click, extract_order_summary

logger = structlog.get_logger()


# Global browser instance (managed by agent service)
_browser: BrowserController = None


def set_browser(browser: BrowserController) -> None:
    """Set the global browser instance for nodes to use"""
    global _browser
    _browser = browser


def get_browser() -> BrowserController:
    """Get the global browser instance"""
    global _browser
    if _browser is None:
        raise RuntimeError("Browser not initialized. Call set_browser() first.")
    return _browser


async def observer_node(state: AgentState) -> AgentState:
    """
    Observer Node: Captures the current state of the page
    
    - Takes screenshot
    - Injects visual markers
    - Updates state with page information
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with screenshot and markers
    """
    logger.info("Observer node starting", iteration=state["iterations"])
    
    try:
        set_status(state, "observing")
        
        browser = get_browser()
        
        # Get current URL
        current_url = await browser.get_url()
        state["current_url"] = current_url
        
        logger.info("Observing page", url=current_url)
        
        # Remove old markers if any
        try:
            await remove_markers(browser.page)
        except:
            pass
        
        # Inject markers on interactive elements
        markers_map = await inject_markers(browser.page)
        state["markers_map"] = markers_map
        
        logger.info("Markers injected", count=len(markers_map))
        
        # Take screenshot with markers
        screenshot = await browser.take_screenshot()
        state["screenshot_base64"] = screenshot
        
        # Add observation message
        message = AIMessage(
            content=f"Observed page: {current_url}. Found {len(markers_map)} interactive elements."
        )
        add_message(state, message)
        
        logger.info("Observer node complete", 
                   url=current_url,
                   markers=len(markers_map))
        
        return state
        
    except Exception as e:
        logger.error("Observer node failed", error=str(e))
        set_error(state, f"Observation failed: {str(e)}")
        return state


async def reasoning_node(state: AgentState) -> AgentState:
    """
    Reasoning Node: Analyzes screenshot and decides next action
    
    - Sends screenshot to Gemini vision model
    - Gets next action decision
    - Updates state with planned action
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with planned action
    """
    logger.info("Reasoning node starting", iteration=state["iterations"])
    
    try:
        set_status(state, "reasoning")
        
        # Get vision analyzer
        vision_analyzer = get_vision_analyzer()
        
        # Get recent actions to avoid loops
        recent_actions = get_recent_actions(state, count=5)
        
        logger.info("Analyzing page with vision AI",
                   markers_count=len(state["markers_map"]),
                   history_length=len(recent_actions))
        
        # Analyze page and get next action
        action = await vision_analyzer.analyze_page(
            screenshot_base64=state["screenshot_base64"],
            markers_map=state["markers_map"],
            user_goal=state["user_goal"],
            action_history=recent_actions,
            current_url=state.get("current_url", "")
        )
        
        # Store planned action
        state["last_action"] = action
        
        # Add reasoning message
        reasoning = action.get("reasoning", "No reasoning provided")
        action_type = action.get("action", "unknown")
        target = action.get("target", "N/A")
        
        message = AIMessage(
            content=f"Reasoning: {reasoning}\nPlanned action: {action_type} on [{target}]"
        )
        add_message(state, message)
        
        logger.info("Reasoning complete",
                   action=action_type,
                   target=target,
                   reasoning=reasoning[:100])
        
        # Check if action is "done"
        if action_type == "done":
            set_status(state, "complete")
        
        return state
        
    except Exception as e:
        logger.error("Reasoning node failed", error=str(e))
        set_error(state, f"Reasoning failed: {str(e)}")
        return state


async def action_node(state: AgentState) -> AgentState:
    """
    Action Node: Executes the planned action
    
    - Clicks elements
    - Types text
    - Scrolls page
    - Updates action history
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state after action execution
    """
    logger.info("Action node starting", iteration=state["iterations"])
    
    try:
        set_status(state, "executing")
        
        browser = get_browser()
        action = state["last_action"]
        
        if not action:
            logger.warning("No action to execute")
            return state
        
        action_type = action.get("action")
        target = action.get("target")
        value = action.get("value")
        
        logger.info("Executing action",
                   type=action_type,
                   target=target,
                   value=value[:50] if value else None)
        
        # Execute based on action type
        if action_type == "click":
            await execute_click(browser, state, target)
        
        elif action_type == "type":
            await execute_type(browser, state, target, value)
        
        elif action_type == "scroll":
            await execute_scroll(browser, state)
        
        elif action_type == "done":
            logger.info("Mission complete!")
            set_status(state, "complete")
        
        else:
            logger.warning("Unknown action type", action_type=action_type)
        
        # Add to action history
        add_action(state, action)
        
        # Increment iteration counter
        increment_iteration(state)
        
        # Wait a bit for page to settle
        await asyncio.sleep(1)
        
        # Remove markers before next observation
        await remove_markers(browser.page)
        
        logger.info("Action node complete",
                   iteration=state["iterations"])
        
        return state
        
    except Exception as e:
        logger.error("Action node failed", error=str(e))
        set_error(state, f"Action execution failed: {str(e)}")
        return state


async def execute_click(browser: BrowserController, state: AgentState, target: int) -> None:
    """
    Execute click action on target element
    
    Args:
        browser: Browser controller
        state: Current agent state
        target: Marker number to click
    """
    try:
        # Get selector and element info for target
        selector = await get_element_by_marker(browser.page, state["markers_map"], target)
        
        if not selector:
            raise ValueError(f"Could not find element for marker [{target}]")
        
        # Get element text for safety check
        element_info = state["markers_map"].get(target, {})
        element_text = element_info.get('text', '') or element_info.get('aria_label', '')
        
        # Safety check before clicking
        safety_check = await check_before_click(
            browser.page,
            state["screenshot_base64"],
            element_text
        )
        
        if safety_check.get('requires_approval', False):
            # Requires human approval
            logger.warning("Human approval required", 
                         marker=target,
                         reason=safety_check.get('reason'))
            
            state["approval_required"] = True
            
            # Add approval request message
            checkout_info = safety_check.get('checkout_info')
            if checkout_info:
                summary = extract_order_summary(checkout_info)
                message = AIMessage(content=f"⚠️ APPROVAL REQUIRED\n\n{summary}")
            else:
                message = AIMessage(content=f"⚠️ APPROVAL REQUIRED\n\n{safety_check.get('reason')}")
            
            add_message(state, message)
            return
        
        logger.info("Clicking element", marker=target, selector=selector)
        
        # Wait for element to be stable (not animating)
        await asyncio.sleep(0.5)
        
        # Try multiple approaches
        try:
            # First try: Wait for element to be ready, then click
            await browser.page.wait_for_selector(selector, state="visible", timeout=5000)
            await browser.page.click(selector, timeout=5000)
        except Exception as e1:
            logger.warning(f"Direct click failed: {e1}, trying JavaScript click")
            try:
                # Second try: JavaScript click (bypasses some overlays)
                await browser.page.evaluate(f"""
                    const element = document.querySelector('{selector}');
                    if (element) element.click();
                """)
            except Exception as e2:
                logger.warning(f"JavaScript click failed: {e2}, trying force click")
                try:
                    # Third try: force click (ignores actionability checks)
                    await browser.page.click(selector, force=True, timeout=5000)
                except Exception as e3:
                    logger.error(f"Force click failed: {e3}")
                    raise
        
        logger.info("Click successful", marker=target)
        
        # Add success message
        message = AIMessage(content=f"✓ Clicked element [{target}]")
        add_message(state, message)
        
    except Exception as e:
        logger.error("Click failed", marker=target, error=str(e))
        message = AIMessage(content=f"✗ Failed to click element [{target}]: {str(e)}")
        add_message(state, message)


async def execute_type(browser: BrowserController, state: AgentState, target: int, value: str) -> None:
    """
    Execute type action on input element
    
    Args:
        browser: Browser controller
        state: Current agent state
        target: Marker number of input field
        value: Text to type
    """
    try:
        # Get selector for target
        selector = await get_element_by_marker(browser.page, state["markers_map"], target)
        
        if not selector:
            raise ValueError(f"Could not find element for marker [{target}]")
        
        logger.info("Typing into element", marker=target, selector=selector, value=value)
        
        # Wait for element to be ready
        await browser.page.wait_for_selector(selector, state="visible", timeout=5000)
        
        # Focus on the element first
        await browser.page.focus(selector)
        await asyncio.sleep(0.3)
        
        # Clear existing value first
        await browser.page.fill(selector, "")
        await asyncio.sleep(0.2)
        
        # Type the text (human-like with delays)
        await browser.page.type(selector, value, delay=50)
        await asyncio.sleep(0.5)
        
        # Press Enter to submit (common for search boxes)
        await browser.page.press(selector, "Enter")
        
        logger.info("Type successful", marker=target)
        
        # Add success message
        message = AIMessage(content=f"✓ Typed '{value}' into element [{target}] and pressed Enter")
        add_message(state, message)
        
    except Exception as e:
        logger.error("Type failed", marker=target, error=str(e))
        message = AIMessage(content=f"✗ Failed to type into element [{target}]: {str(e)}")
        add_message(state, message)


async def execute_scroll(browser: BrowserController, state: AgentState) -> None:
    """
    Execute scroll action
    
    Args:
        browser: Browser controller
        state: Current agent state
    """
    try:
        logger.info("Scrolling page")
        
        # Scroll down 500 pixels
        await browser.scroll(direction="down", amount=500)
        
        logger.info("Scroll successful")
        
        # Add success message
        message = AIMessage(content="✓ Scrolled down to see more content")
        add_message(state, message)
        
    except Exception as e:
        logger.error("Scroll failed", error=str(e))
        message = AIMessage(content=f"✗ Failed to scroll: {str(e)}")
        add_message(state, message)

