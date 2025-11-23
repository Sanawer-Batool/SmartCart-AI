# 🎯 START HERE - Quick Guide for SmartCart AI

## 🚀 How to Use Your AI Shopping Assistant

### Step 1️⃣: Start Backend (First Terminal)

```bash
cd "D:\All Projects\SmartCart AI\backend"
venv\Scripts\activate
python app.py
```

**Wait for**: `Uvicorn running on http://0.0.0.0:8000` ✅

---

### Step 2️⃣: Start Frontend (Second Terminal)

```bash
cd "D:\All Projects\SmartCart AI\frontend"
npm run dev
```

**Wait for**: `Local: http://localhost:3000` ✅

---

### Step 3️⃣: Open Browser

Go to: **http://localhost:3000**

---

## 🛍️ Example: Find Cheap Laptops on Amazon

### What You Type:

**Website URL:**
```
https://amazon.com
```

**Goal:**
```
Find cheap laptops under $500
```

### Then Click: **[Start Mission]**

---

## 👀 What Happens Next

The AI agent will:

1. 🌐 Open amazon.com
2. 🔍 Find the search box
3. ⌨️ Type "cheap laptops under $500"
4. 🖱️ Click search
5. 📊 Browse results
6. 💬 Tell you what it found

All automatically! You just watch! ✨

---

## 🎮 Try These Examples

### Easy Test (Start Here!)
```
URL:  https://example.com
Goal: Find the main heading on this page
```
**Why**: Simple test to see if everything works

---

### Amazon Search
```
URL:  https://amazon.com
Goal: Search for wireless headphones
```

---

### With Price Limit
```
URL:  https://amazon.com
Goal: Find gaming keyboards under $75
```

---

### Specific Product
```
URL:  https://bestbuy.com
Goal: Find iPhone 15 Pro Max
```

---

### Compare Products
```
URL:  https://amazon.com
Goal: Show me the top 3 rated wireless earbuds
```

---

## 🎨 The Interface

```
┌─────────────────────────────────────────────────────────────┐
│  🛒 SmartCart AI                      [🟢 Connected]        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  LEFT SIDE: Chat Messages            RIGHT SIDE: Live View  │
│  ─────────────────────               ──────────────────     │
│  • Your goal                         • Screenshot of what   │
│  • Agent's thoughts                    the agent sees       │
│  • Actions taken                     • Red numbered labels  │
│  • What it found                       on clickable items   │
│  • Status updates                    • Current URL          │
│                                      • Iteration counter    │
│  [🛑 Stop Button]                                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔴 Important Notes

### First Time Setup

**Before first use**, you need to install dependencies:

**Backend (Terminal 1):**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

**Frontend (Terminal 2):**
```bash
cd frontend
npm install
```

**Only need to do this once!** After that, just run the startup commands.

---

### Your API Key is Already Configured

The file `backend/.env` should contain:
```
GOOGLE_API_KEY=AIzaSyADh8OOzgqaxnbvAtjcyt32d8RGqSaYyqE
```

If the file doesn't exist, create it with that content.

---

## 🆘 Quick Fixes

### Problem: "Can't connect"
**Solution**: Make sure BOTH terminals are running (backend + frontend)

### Problem: "Module not found"
**Solution**: 
```bash
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

### Problem: "npm: command not found"
**Solution**: Install Node.js from https://nodejs.org/

### Problem: Backend shows errors
**Solution**: Check if .env file exists with your API key

---

## ✅ Success Checklist

Before starting a mission, verify:

- [ ] Backend terminal shows "Uvicorn running"
- [ ] Frontend terminal shows "Local: http://localhost:3000"
- [ ] Browser opened to http://localhost:3000
- [ ] Top right shows "🟢 Connected"
- [ ] You can type in the URL and Goal fields

If all checked, you're ready! 🚀

---

## 🎯 Your First Mission - Step by Step

1. **Open browser** → http://localhost:3000

2. **You'll see two input boxes:**
   - Top box: "Website URL"
   - Bottom box: "Goal"

3. **Click in the URL box** and type:
   ```
   https://amazon.com
   ```

4. **Click in the Goal box** and type:
   ```
   Find cheap laptops under $500
   ```

5. **Click the blue "Start Mission" button**

6. **Watch the left side** for messages from the agent

7. **Watch the right side** for live screenshots

8. **Click "Stop" anytime** to cancel the mission

That's it! 🎉

---

## 🌟 Cool Things to Watch For

- **Red numbered labels** on the screenshot (Set-of-Marks)
- **Agent's reasoning** ("I found the search box at [5]")
- **Action messages** ("✓ Clicked element [8]")
- **Screenshot updates** as it navigates
- **Iteration counter** showing progress

---

## 💡 Pro Tips

1. **Be specific in your goal**
   - ✅ Good: "Find wireless headphones under $100"
   - ❌ Vague: "Look for stuff"

2. **Start simple**
   - Try example.com first to test
   - Then move to real shopping sites

3. **Watch the agent learn**
   - It might take a few tries
   - Each action is logged in the chat

4. **Use Stop button**
   - Don't worry about stopping it
   - It won't complete purchases without approval

5. **Check the screenshots**
   - The red numbers show what it can click
   - The agent references these numbers

---

## 🎊 You're Ready!

Your AI shopping assistant is waiting at:

### **http://localhost:3000**

Go try it now! 🚀

Start with a simple test, then try finding those cheap laptops on Amazon!

---

**Questions?** Check the other documentation files:
- `QUICKSTART.md` - Detailed setup
- `README.md` - Full documentation
- `SETUP_INSTRUCTIONS.md` - Troubleshooting

**Happy shopping! 🛍️**

