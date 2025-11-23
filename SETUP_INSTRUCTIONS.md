# 🛠️ Setup Instructions for SmartCart AI

## Your Gemini API Key
Your API key has been configured in the backend: `AIzaSyADh8OOzgqaxnbvAtjcyt32d8RGqSaYyqE`

**Note:** In production, keep API keys secret! This is included for development convenience only.

---

## 🚀 Step-by-Step Setup

### 1️⃣ Backend Setup

Open a terminal in the project directory:

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
venv\Scripts\Activate.ps1
# On Windows (Command Prompt):
venv\Scripts\activate.bat
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
python -m playwright install chromium

# Optional: Install system dependencies (Linux only)
# python -m playwright install-deps
```

### 2️⃣ Create .env File

Create a file named `.env` in the `backend` directory with this content:

```bash
GOOGLE_API_KEY=AIzaSyADh8OOzgqaxnbvAtjcyt32d8RGqSaYyqE
HOST=0.0.0.0
PORT=8000
DEBUG=True
HEADLESS=True
BROWSER_TIMEOUT=30000
```

Or simply copy the example:
```bash
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

Then edit `.env` if needed.

### 3️⃣ Test Backend

```bash
# Make sure you're in backend directory with venv activated
python app.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Visit http://localhost:8000/health to verify it's working.

Press Ctrl+C to stop.

### 4️⃣ Frontend Setup

Open a **new terminal**:

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install
```

This will download all Node.js packages (may take a few minutes).

### 5️⃣ Test Frontend

```bash
# In the frontend directory
npm run dev
```

You should see:
```
- Local:        http://localhost:3000
- Network:      http://192.168.x.x:3000
```

Visit http://localhost:3000 to see the interface.

---

## 🎯 Running Both Services

### Option 1: Two Terminals (Recommended for Development)

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate  # or source venv/bin/activate on Mac/Linux
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Option 2: Quick Start Script

**Windows:**
```bash
# From project root
start-all.bat
```

**Mac/Linux:**
```bash
# From project root
chmod +x start-all.sh
./start-all.sh
```

This opens two new windows with backend and frontend running.

---

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] Backend responds at http://localhost:8000
- [ ] API docs load at http://localhost:8000/docs
- [ ] Health check returns status "healthy"
- [ ] Frontend loads at http://localhost:3000
- [ ] Connection indicator shows "Connected"
- [ ] Can enter URL and goal
- [ ] "Start Mission" button is clickable

---

## 🧪 Test Run

1. Open http://localhost:3000
2. Enter:
   - **URL:** `https://example.com`
   - **Goal:** `Find the main heading on this page`
3. Click "Start Mission"
4. You should see:
   - Messages in the left panel
   - A screenshot in the right panel
   - Agent taking actions

---

## 🐛 Troubleshooting

### Backend won't start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`
```bash
# Make sure venv is activated (you should see (venv) in terminal)
# Then reinstall:
pip install -r requirements.txt
```

**Error:** `playwright._impl._errors.Error: Executable doesn't exist`
```bash
python -m playwright install chromium
```

**Error:** `ValueError: GOOGLE_API_KEY is required`
```bash
# Check .env file exists in backend/ directory
# Verify it contains: GOOGLE_API_KEY=AIzaSyADh8OOzgqaxnbvAtjcyt32d8RGqSaYyqE
```

### Frontend won't start

**Error:** `Cannot find module 'next'`
```bash
# Delete node_modules and reinstall
rm -rf node_modules  # or: rmdir /s node_modules on Windows
npm install
```

**Error:** `Port 3000 is already in use`
```bash
# Kill the process using port 3000, or use a different port:
PORT=3001 npm run dev
```

### WebSocket connection fails

1. Make sure backend is running on port 8000
2. Check browser console for errors (F12)
3. Verify no firewall blocking localhost connections
4. Try restarting both services

### Gemini API errors

**Error:** `ResourceExhausted` or `429`
- You hit the free tier rate limit (15 requests/minute)
- Wait a minute and try again
- Consider adding delays between actions

**Error:** `InvalidArgument`
- Check your API key is correct
- Verify .env file is properly formatted
- Try regenerating key at https://aistudio.google.com/app/apikey

---

## 🎮 Using the Application

### Basic Workflow

1. **Start both services** (backend + frontend)
2. **Open frontend** at http://localhost:3000
3. **Enter website URL** - Any public website works
4. **Describe your goal** - What you want the agent to do
5. **Click Start Mission** - Watch it work!
6. **Monitor progress** - See agent's thoughts and actions
7. **Stop if needed** - Click the red Stop button

### Example Goals

**Simple:**
```
URL: https://example.com
Goal: Read the main heading
```

**Search:**
```
URL: https://amazon.com
Goal: Search for wireless headphones
```

**Navigation:**
```
URL: https://github.com
Goal: Find the Explore section
```

**Complex:**
```
URL: https://news.ycombinator.com
Goal: Find the top story and click on it
```

---

## 📚 Next Steps

Now that everything is set up:

1. ✅ Try different websites and goals
2. ✅ Read the full documentation in README.md
3. ✅ Explore the code to understand how it works
4. ✅ Check out PROJECT_SUMMARY.md for implementation details
5. ✅ Experiment with modifications

---

## 🔒 Security Note

The API key in this project is included for development convenience. 

**For production:**
1. Never commit .env files to git
2. Use environment variables or secret management
3. Rotate keys regularly
4. Monitor usage at Google AI Studio

---

## 💡 Tips

- **First run is slower** - Gemini needs to process images
- **Use specific goals** - "Find X" is better than "Browse"
- **Monitor iterations** - Agent stops at 20 steps max
- **Check logs** - Backend terminal shows detailed info
- **Use headless mode** - Set `HEADLESS=False` in .env to see browser

---

## 🆘 Still Having Issues?

1. **Check all requirements:**
   - Python 3.10+ installed?
   - Node.js 18+ installed?
   - Virtual environment activated?
   - All dependencies installed?

2. **Verify file structure:**
   ```
   SmartCart AI/
   ├── backend/
   │   ├── venv/  (should exist after setup)
   │   ├── .env   (you created this)
   │   └── ...
   └── frontend/
       ├── node_modules/  (should exist after npm install)
       └── ...
   ```

3. **Check terminal output** for specific error messages

4. **Review documentation:**
   - QUICKSTART.md
   - README.md
   - backend/README.md
   - frontend/README.md

---

## ✅ You're All Set!

If you can:
- ✅ Access http://localhost:8000/docs
- ✅ Access http://localhost:3000
- ✅ See "Connected" status in frontend
- ✅ Start a mission

**Congratulations! SmartCart AI is ready to use! 🎉**

---

*Last updated: 2025-01-22*

