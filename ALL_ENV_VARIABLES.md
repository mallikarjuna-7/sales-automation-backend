# Complete Environment Variables List

## ✅ YES - Your Understanding is Correct!

**On Render (Production):**
- Upload ALL environment variables to Render website
- `config.py` will read from Render's environment variables

**On Local (Development):**
- Keep values in `.env` file
- `config.py` will read from `.env` file

**The same `config.py` works for both!** It automatically picks the right source.

---

## 📋 All Environment Variables Currently Used

Based on your `.env` file and `config.py`, here's the complete list:

### 1. MONGODB_URL
- **Type:** Required (no default)
- **Your current value:** `mongodb+srv://smallikarjun713_db_user:lIOKUAVgJX47lx3X@kabaddi.iaqsvzl.mongodb.net/kabaddi?retryWrites=true&w=majority&appName=kabaddi`
- **Add to Render:** ✅ YES

### 2. DB_NAME
- **Type:** Optional
- **Default in config.py:** `sales_automation`
- **Your current value:** `kabaddi`
- **Add to Render:** ✅ YES (use `kabaddi`)

### 3. PORT
- **Type:** Optional
- **Default in config.py:** `8000`
- **Your current value:** `8000`
- **Add to Render:** ❌ NO (Render sets this automatically)

### 4. DEBUG
- **Type:** Optional
- **Default in config.py:** `False`
- **Your current value:** `True`
- **Add to Render:** ✅ YES (set to `False`)

### 5. ML_SERVICE_URL
- **Type:** Optional
- **Default in config.py:** `http://localhost:8080`
- **Your current value:** Not set in your `.env`
- **Add to Render:** ⚠️ Optional (default is fine)

### 6. MAIL_USERNAME
- **Type:** Optional
- **Default in config.py:** `""` (empty string)
- **Your current value:** `mrewards7745@gmail.com`
- **Add to Render:** ⚠️ If you need email functionality

### 7. MAIL_PASSWORD
- **Type:** Optional
- **Default in config.py:** `""` (empty string)
- **Your current value:** `jowo yrvh rvrk hygk`
- **Add to Render:** ⚠️ If you need email functionality

### 8. MAIL_FROM
- **Type:** Optional
- **Default in config.py:** `""` (empty string)
- **Your current value:** `mrewards7745@gmail.com`
- **Add to Render:** ⚠️ If you need email functionality

### 9. MAIL_PORT
- **Type:** Optional
- **Default in config.py:** `587`
- **Your current value:** `587`
- **Add to Render:** ❌ NO (default matches your value)

### 10. MAIL_SERVER
- **Type:** Optional
- **Default in config.py:** `smtp.gmail.com`
- **Your current value:** `smtp.gmail.com`
- **Add to Render:** ❌ NO (default matches your value)

### 11. MAIL_FROM_NAME
- **Type:** Optional
- **Default in config.py:** `Sales Automation`
- **Your current value:** Not set in your `.env`
- **Add to Render:** ❌ NO (default is fine)

### 12. MAIL_STARTTLS
- **Type:** Optional
- **Default in config.py:** `True`
- **Your current value:** Not set in your `.env`
- **Add to Render:** ❌ NO (default is fine)

### 13. MAIL_SSL_TLS
- **Type:** Optional
- **Default in config.py:** `False`
- **Your current value:** Not set in your `.env`
- **Add to Render:** ❌ NO (default is fine)

---

## 🚀 For Render - Copy-Paste Ready

### Minimum (3 variables):
```
MONGODB_URL=mongodb+srv://smallikarjun713_db_user:lIOKUAVgJX47lx3X@kabaddi.iaqsvzl.mongodb.net/kabaddi?retryWrites=true&w=majority&appName=kabaddi
DB_NAME=kabaddi
DEBUG=False
```

### Add Email Support (3 more variables):
```
MAIL_USERNAME=mrewards7745@gmail.com
MAIL_PASSWORD=jowo yrvh rvrk hygk
MAIL_FROM=mrewards7745@gmail.com
```

---

## 🏠 For Local - Keep in .env

Your current `.env` file:
```env
MONGODB_URL=mongodb+srv://smallikarjun713_db_user:lIOKUAVgJX47lx3X@kabaddi.iaqsvzl.mongodb.net/kabaddi?retryWrites=true&w=majority&appName=kabaddi
DB_NAME=kabaddi
PORT=8000
DEBUG=True

# SMTP Settings
MAIL_USERNAME=mrewards7745@gmail.com
MAIL_PASSWORD=jowo yrvh rvrk hygk
MAIL_FROM=mrewards7745@gmail.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
```

---

## 🔄 How It Works

```
┌─────────────────────────────────────────────────┐
│  config.py (Same file for both environments)   │
└─────────────────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
┌───────────────┐          ┌────────────────┐
│  LOCAL DEV    │          │  RENDER PROD   │
├───────────────┤          ├────────────────┤
│ Reads from:   │          │ Reads from:    │
│ .env file     │          │ Render env vars│
└───────────────┘          └────────────────┘
```

**Same code, different sources!** ✨

---

## ✅ Summary

**Your understanding is 100% correct:**

1. **Render (Production):** Upload all variables to Render website → `config.py` reads them
2. **Local (Development):** Keep variables in `.env` file → `config.py` reads them

**No code changes needed!** The `pydantic-settings` library in `config.py` automatically:
- Checks environment variables first (Render)
- Falls back to `.env` file (Local)
- Uses defaults from `config.py` if neither exists

---

## 📊 Quick Decision Matrix

| Variable | Add to Render? | Reason |
|----------|---------------|---------|
| `MONGODB_URL` | ✅ YES | Required, no default |
| `DB_NAME` | ✅ YES | Your value differs from default |
| `DEBUG` | ✅ YES | Change to `False` for production |
| `MAIL_USERNAME` | ⚠️ If needed | For email functionality |
| `MAIL_PASSWORD` | ⚠️ If needed | For email functionality |
| `MAIL_FROM` | ⚠️ If needed | For email functionality |
| `PORT` | ❌ NO | Render auto-sets |
| `MAIL_SERVER` | ❌ NO | Default matches |
| `MAIL_PORT` | ❌ NO | Default matches |
| `ML_SERVICE_URL` | ❌ NO | Default is fine |
| `MAIL_FROM_NAME` | ❌ NO | Default is fine |
| `MAIL_STARTTLS` | ❌ NO | Default is fine |
| `MAIL_SSL_TLS` | ❌ NO | Default is fine |

**Total to add:** 3-6 variables (depending on if you need email)
