# FocusFlow-AI - Complete Setup Guide 🚀

## ✅ What You Have

Since you already have API keys for both Gemini and Groq, you're all set! Follow these simple steps:

---

## 📋 Step-by-Step Setup

### **Step 1: Install Python Dependencies**

Open your terminal/command prompt and run:

```bash
pip install flask flask-cors python-dotenv google-generativeai groq
```

**OR** install from requirements.txt:

```bash
pip install -r requirements.txt
```

If you get permission errors, try:

```bash
pip install -r requirements.txt --user
```

---

### **Step 2: Add Your API Keys**

Open the `.env` file and add your API keys:

```bash
# Choose ONE (Gemini is recommended)

# Option 1: Google Gemini (RECOMMENDED)
GEMINI_API_KEY=your_actual_gemini_key_here

# Option 2: Groq
GROQ_API_KEY=your_actual_groq_key_here
```

**Important:** 
- Replace `your_actual_gemini_key_here` with your real API key
- Remove the `your_` prefix - paste the actual key
- You only need ONE key (Gemini OR Groq, not both)

**Example:**
```bash
GEMINI_API_KEY=AIzaSyD1234567890abcdefghijklmnopqrstuv
```

---

### **Step 3: Start the Backend**

In your terminal, run:

```bash
python backend.py
```

You should see:

```
============================================================
FocusFlow-AI Backend - FREE AI Edition
============================================================
✓ AI Provider: GEMINI
✓ Model: gemini-pro
✓ Cost: $0.00 (FREE)
✓ Server: http://localhost:5000
============================================================
```

**Keep this terminal window open!**

---

### **Step 4: Open the App**

Open your web browser and go to:

```
http://localhost:5000
```

You should see the FocusFlow-AI interface!

---

## 🎯 How to Test It's Working

### **Test 1: Chat with AI**

1. Click **"Ask-AI"** in the navigation
2. Type: `How should I organize my study schedule?`
3. Press Enter

You should get an AI-generated response!

### **Test 2: Generate Schedule**

1. Click **"Home"**
2. Click **"Tell Workflow"** button
3. Type:
   ```
   I need to study Math, Physics, and Chemistry for finals. 
   I have 2 weeks and prefer morning sessions. Math is my priority.
   ```
4. Click **"Generate Schedule"**

The AI will create a personalized schedule!

### **Test 3: Check Backend Connection**

1. Open browser console (F12 or right-click → Inspect)
2. Go to **Console** tab
3. You should see:
   ```
   FocusFlow-AI Backend Connected ✓
   Status: healthy
   AI Provider: gemini
   AI Enabled: YES ✓
   ```

---

## 🐛 Troubleshooting

### **Problem: "Module not found" errors**

**Solution:** Install the missing package:

```bash
# If Flask is missing
pip install flask flask-cors

# If AI library is missing
pip install google-generativeai groq

# Or install everything
pip install -r requirements.txt
```

---

### **Problem: Backend says "AI Provider: fallback"**

**Cause:** Your API key isn't being read

**Solution:**

1. Check `.env` file exists in the same folder as `backend.py`
2. Make sure you saved the file after editing
3. Check for typos in the key
4. Try setting the environment variable directly:

   **Windows (Command Prompt):**
   ```cmd
   set GEMINI_API_KEY=your_key_here
   python backend.py
   ```

   **Windows (PowerShell):**
   ```powershell
   $env:GEMINI_API_KEY="your_key_here"
   python backend.py
   ```

   **Mac/Linux:**
   ```bash
   export GEMINI_API_KEY=your_key_here
   python backend.py
   ```

---

### **Problem: Port 5000 already in use**

**Solution:** Kill the process or use a different port:

**Option 1 - Kill existing process:**

**Windows:**
```cmd
netstat -ano | findstr :5000
taskkill /PID <process_id> /F
```

**Mac/Linux:**
```bash
lsof -ti:5000 | xargs kill -9
```

**Option 2 - Use different port:**
```bash
# In terminal
export PORT=8000
python backend.py

# Then open: http://localhost:8000
```

---

### **Problem: "CORS error" in browser console**

**Solution:** This means backend isn't running

1. Make sure you ran `python backend.py`
2. Check the terminal for errors
3. Try restarting the backend

---

### **Problem: AI responses seem generic/not working**

**Check these:**

1. **Is your API key valid?**
   - Test it at: https://makersuite.google.com/app/apikey
   
2. **Check backend logs:**
   - Look for errors in the terminal running `backend.py`
   
3. **Verify AI is enabled:**
   - Open: http://localhost:5000/api/health
   - Should show: `"ai_enabled": true`

---

## 📁 Project Structure

Make sure you have these files in the same folder:

```
focusflow-ai/
├── backend.py          ← Backend server
├── index.html          ← Main page
├── styles.css          ← Styling
├── script.js           ← Frontend logic
├── requirements.txt    ← Dependencies
├── .env               ← Your API keys (CREATE THIS!)
└── focusflow.db       ← Database (auto-created)
```

---

## 🎨 Quick Test Commands

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Check Python version (should be 3.8+)
python --version

# 3. Test backend API directly
python -c "import google.generativeai as genai; print('Gemini OK!')"

# 4. Start backend
python backend.py

# 5. Open in browser
# Go to: http://localhost:5000
```

---

## 💡 Pro Tips

1. **Keep backend running** - Don't close the terminal window
2. **Refresh browser** - If changes don't appear, refresh (Ctrl+R / Cmd+R)
3. **Check console** - Press F12 to see errors
4. **Use Gemini** - It's faster and more generous than Groq
5. **Database resets** - Delete `focusflow.db` to start fresh

---

## 🎯 Verification Checklist

- [ ] Python 3.8+ installed
- [ ] All packages installed (`pip install -r requirements.txt`)
- [ ] `.env` file created with API key
- [ ] Backend running (`python backend.py`)
- [ ] Browser open at `http://localhost:5000`
- [ ] No errors in browser console (F12)
- [ ] AI responses working in Ask-AI page

---

## 📞 Still Having Issues?

### Quick Diagnostic:

1. **Run this command:**
   ```bash
   python backend.py
   ```

2. **Copy the output** from the terminal

3. **Check what it says:**
   - If it says `✓ AI Provider: GEMINI` → You're good!
   - If it says `✓ AI Provider: fallback` → API key not loaded
   - If you see errors → Share them for help

### Common Error Messages:

**"No module named 'flask'"**
→ Run: `pip install flask flask-cors`

**"No module named 'google.generativeai'"**
→ Run: `pip install google-generativeai`

**"Invalid API key"**
→ Check your API key is correct in `.env`

**"Address already in use"**
→ Port 5000 is taken, use different port or kill process

---

## 🚀 You're All Set!

Once you see the backend running with AI enabled, just:

1. Keep terminal open
2. Open browser to `http://localhost:5000`
3. Start using the app!

**Enjoy your FocusFlow-AI! 🎉**
