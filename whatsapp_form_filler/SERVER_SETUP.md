# WhatsApp Form Auto-Fill System - Server Deployment

## 🎯 Production Setup (Server/Always-On Mode)

This system monitors WhatsApp Web for Microsoft Forms links and automatically fills them.

### 📋 Prerequisites

- ✅ Windows Server or PC (always on)
- ✅ Chrome installed
- ✅ Python 3.11+ with venv
- ✅ Already logged into Microsoft account in Chrome

---

## 🚀 Quick Start (Server)

### Step 1: Start Chrome in Debug Mode

Double-click or run:
```batch
start_chrome.bat
```

This will:
- Close any existing Chrome instances
- Open Chrome with remote debugging enabled
- Keep it running in the background

**Keep this window open!**

### Step 2: Setup WhatsApp Web

1. Chrome will open automatically
2. Go to: https://web.whatsapp.com
3. Scan QR code with your phone
4. Keep this tab open

### Step 3: Start the Monitor

In a new terminal:
```powershell
.\venv\Scripts\python.exe watch_whatsapp.py
```

This will:
- Connect to the running Chrome
- Monitor WhatsApp for form links
- Automatically process them
- Keep running 24/7

---

## 📊 What Happens When a Link Arrives?

1. 📱 **Link detected** in WhatsApp
2. 🌐 **New tab opens** in Chrome
3. ✍️ **Form auto-filled:**
   - Name: Halil Eren Kepiç
   - ID: 2306002093
   - Attendance: ✅
4. 📤 **Form submitted**
5. 📸 **Screenshots saved** to `logs/`
6. 🗙 **Tab closed** (Chrome stays open)
7. 👁️ **Monitor continues** watching

---

## 🔧 Configuration

Edit `.env` file:
```env
# Student Information
STUDENT_NAME=Halil Eren Kepiç
STUDENT_ID=2306002093

# System Settings
HEADLESS_MODE=false
SCREENSHOT_ON_SUCCESS=true
SCREENSHOT_ON_ERROR=true
```

---

## 📂 File Structure

```
whatsapp_form_filler/
├── start_chrome.bat           # Start Chrome in debug mode
├── watch_whatsapp.py          # WhatsApp monitor (main service)
├── .env                       # Configuration
├── logs/                      # Screenshots and logs
│   ├── YYYYMMDD_HHMMSS_before.png
│   ├── YYYYMMDD_HHMMSS_after.png
│   └── YYYYMMDD_HHMMSS_submitted.png
└── data/
    └── whatsapp_form_filler.db  # Submission history
```

---

## 🛠️ Troubleshooting

### Chrome won't start
```batch
# Kill all Chrome processes
taskkill /F /IM chrome.exe

# Start again
start_chrome.bat
```

### Monitor can't connect
Check:
1. Chrome is running (`start_chrome.bat`)
2. Port 9222 is not blocked
3. Run: `netstat -an | findstr 9222`

### Forms not detected
1. Make sure WhatsApp Web tab is open
2. Check logs for errors
3. Verify link contains `forms.office.com`

### Login required
1. Open Chrome normally (NOT debug mode)
2. Go to forms.office.com
3. Login with student account
4. Close Chrome
5. Run `start_chrome.bat` again

---

## 🔄 Automatic Restart (Optional)

Create `monitor_service.bat`:
```batch
@echo off
:loop
echo Starting monitor...
.\venv\Scripts\python.exe watch_whatsapp.py
echo Monitor stopped. Restarting in 10 seconds...
timeout /t 10
goto loop
```

---

## 📝 System Requirements

- **RAM:** 2GB minimum (Chrome + Playwright)
- **Disk:** 500MB for logs and screenshots
- **Network:** Stable internet connection
- **OS:** Windows 10/11 or Server 2016+

---

## ⚡ Performance Tips

1. **Cleanup old logs:**
   ```batch
   # Delete logs older than 7 days
   forfiles /p logs /s /m *.png /d -7 /c "cmd /c del @path"
   ```

2. **Monitor memory:**
   Chrome can grow over time. Restart weekly.

3. **Database backup:**
   ```batch
   copy data\whatsapp_form_filler.db data\backup_YYYYMMDD.db
   ```

---

## 🚨 Important Notes

- ⚠️ **Chrome must stay open** - don't close it manually
- ⚠️ **WhatsApp Web must stay logged in**
- ⚠️ **Monitor script must keep running**
- ⚠️ **Server must not sleep/hibernate**

---

## 📞 Support

If issues persist:
1. Check `logs/whatsapp_form_filler.log`
2. Take screenshot of error
3. Note the form URL that failed

---

## 🎉 Success Indicators

You'll know it's working when you see:
```
✅ Connected to Chrome!
✅ Found WhatsApp tab
🚀 Monitoring started!
Watching for Microsoft Forms links...
```

Then when a link arrives:
```
🔔 NEW FORM DETECTED!
✍️  Filling name: Halil Eren Kepiç
✍️  Filling ID: 2306002093
✅ Checking attendance
📤 Submitting form...
🎉 Form submitted successfully!
```

---

**Status:** ✅ System Ready for Production
