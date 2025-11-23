# Amazon Navigation Timeout Fix

## Problem
Navigation to Amazon was timing out with:
```
❌ Error: Navigation failed: Page.goto: Timeout 30000ms exceeded.
Call log:
  - navigating to "https://amazon.com/", waiting until "networkidle"
```

## Root Cause
Amazon's website has **continuous background network activity** (ads, tracking, analytics, etc.) that never stops. The `networkidle` wait strategy waits for 500ms of no network requests, which Amazon never reaches.

## Solution

### 1. Changed Wait Strategy for Amazon
**Before:** Always used `networkidle` (waits for network to be idle)
**After:** Auto-detects Amazon URLs and uses `domcontentloaded` instead

- `domcontentloaded`: Waits for HTML to be parsed (much faster, works for Amazon)
- `networkidle`: Waits for network to be idle (never happens on Amazon)

### 2. Increased Timeout for Amazon
- **Before:** 30 seconds (30000ms)
- **After:** 60 seconds (60000ms) for Amazon URLs

### 3. URL Normalization
Automatically adds `www.` if missing:
- `https://amazon.com/` → `https://www.amazon.com/`
- Works for both `http://` and `https://`

### 4. Longer Wait After Navigation
- Amazon: 2 seconds wait after navigation
- Other sites: 1 second wait

## Code Changes

**File: `backend/browser_controller.py`**

```python
# Auto-detect wait strategy for Amazon
if wait_until is None:
    if is_amazon_url(url):
        wait_until = "domcontentloaded"  # Amazon has continuous network activity
        timeout = 60000  # 60 seconds for Amazon
    else:
        wait_until = "networkidle"
        timeout = Config.BROWSER_TIMEOUT

# Normalize Amazon URLs (add www if missing)
if is_amazon_url(url) and "www." not in url.lower():
    normalized_url = url.replace("amazon.com", "www.amazon.com")
```

## Testing

**Before Fix:**
```
❌ Timeout after 30 seconds
❌ Never reaches networkidle state
```

**After Fix:**
```
✅ Loads in ~3-5 seconds
✅ Uses domcontentloaded (HTML parsed)
✅ Works with or without www.
```

## Usage

The fix is automatic! Just navigate to Amazon:
- `https://amazon.com/` ✅
- `https://www.amazon.com/` ✅
- `http://amazon.com/` ✅

The browser controller will automatically:
1. Detect it's Amazon
2. Use `domcontentloaded` instead of `networkidle`
3. Use 60-second timeout
4. Normalize URL to include `www.`

