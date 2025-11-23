# ⚡ SmartCart AI - Quick Start Guide

Get up and running in 5 minutes!

## 📋 Prerequisites

- Python 3.10+ installed
- Node.js 18+ installed
- A Google Gemini API key ([Get free key here](https://aistudio.google.com/app/apikey))

## 🚀 Installation Steps

### Step 1: Clone or Download

```bash
cd "D:\All Projects\SmartCart AI"
```

### Step 2: Backend Setup

```bash
# Go to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

### Step 3: Configure API Key

Create `backend/.env` file:

```bash
GOOGLE_API_KEY=your_gemini_key_here
```

**Get your free Gemini API key:**
1. Visit https://aistudio.google.com/app/apikey
2. Click "Create API key"
3. Copy and paste into .env file

### Step 4: Frontend Setup

```bash
# Open new terminal
cd frontend

# Install dependencies
npm install
```

### Step 5: Run Everything!

**Option A: Separate Terminals**

Terminal 1 (Backend):
```bash
cd backend
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

python app.py
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

**Option B: One Command (Unix/Mac)**

```bash
chmod +x start-all.sh
./start-all.sh
```

**Option B: One Command (Windows)**

```bash
start-all.bat
```

## 🎮 Using SmartCart AI

1. **Open your browser** → `http://localhost:3000`

2. **Enter a website:**
   ```
   URL: https://amazon.com
   Goal: Find wireless headphones under $100
   ```

3. **Click "Start Mission"**

4. **Watch the magic!** 🎩✨
   - Left panel: Agent's thoughts and actions
   - Right panel: Live view of what it sees

5. **Stop anytime** with the red Stop button

## 📊 What You'll See

```
┌─────────────────────────────────────────────────────────┐
│  SmartCart AI                                [Connected] │
├──────────────────────┬──────────────────────────────────┤
│                      │                                   │
│  CHAT PANEL          │     LIVE VIEW                     │
│  ----------------    │  -------------------------        │
│  👤 Goal: Find...    │  [Screenshot with markers]        │
│  🤖 Observing page   │                                   │
│  🤖 Reasoning...     │  Currently viewing:               │
│  🤖 Clicking [5]     │  amazon.com/search...             │
│  ✅ Found products!  │                                   │
│                      │  Status: executing (Step 3/20)    │
│  [Stop Button]       │                                   │
└──────────────────────┴──────────────────────────────────┘
```

## 🎯 Example Goals to Try

1. **Product Search:**
   ```
   URL: https://amazon.com
   Goal: Find the best rated laptop under $1000
   ```

2. **Specific Item:**
   ```
   URL: https://ebay.com
   Goal: Search for vintage Nike sneakers size 10
   ```

3. **Price Comparison:**
   ```
   URL: https://bestbuy.com
   Goal: Find wireless gaming headsets and show me prices
   ```

## 🔍 Verify It's Working

**Backend Health Check:**
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "gemini_configured": true
}
```

**Visit API Docs:**
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🐛 Common Issues

### "ModuleNotFoundError"
```bash
# Make sure virtual environment is activated
cd backend
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

### "Playwright browser not found"
```bash
playwright install chromium
```

### "WebSocket connection failed"
- Make sure backend is running on port 8000
- Check if another service is using the port
- Try: `netstat -ano | findstr :8000` (Windows)

### "API Key Invalid"
- Check .env file exists in backend/ directory
- Verify no extra spaces in the key
- Get a new key from Google AI Studio

### Frontend won't start
```bash
cd frontend
rm -rf node_modules  # or rmdir /s node_modules on Windows
npm install
npm run dev
```

## 📚 Next Steps

✅ **You're all set!** Now you can:

1. **Experiment** with different websites and goals
2. **Read the full docs** in README.md
3. **Check out the code** to understand how it works
4. **Customize** the agent for your needs

## 🆘 Need Help?

- **Backend Issues:** Check `backend/README.md`
- **Frontend Issues:** Check `frontend/README.md`
- **API Questions:** Visit http://localhost:8000/docs
- **Gemini API:** https://ai.google.dev/docs

## 🎉 Success!

If you see the interface and can start a mission, congratulations! 

You now have a fully functional AI shopping assistant powered by Google Gemini 2.0 Flash! 🚀

---

**Tip:** The first run might be slower as Gemini processes images. Subsequent runs will be faster due to caching!

