# Quick Reference: Environment Variables for Render

## 🎯 Copy-Paste Ready for Render

Based on your current `.env` file, here's exactly what to add in Render's Environment Variables section:

### ✅ Required - Add These First

```
MONGODB_URL=mongodb+srv://smallikarjun713_db_user:lIOKUAVgJX47lx3X@kabaddi.iaqsvzl.mongodb.net/kabaddi?retryWrites=true&w=majority&appName=kabaddi
DB_NAME=kabaddi
DEBUG=False
```

### 📧 Optional - Add If You Need Email Functionality

```
MAIL_USERNAME=mrewards7745@gmail.com
MAIL_PASSWORD=jowo yrvh rvrk hygk
MAIL_FROM=mrewards7745@gmail.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
```

### 🤖 Optional - Add Only If You Have External ML Service

```
ML_SERVICE_URL=http://localhost:8080
```
(Leave this out to use the default)

---

## 📊 Complete Variable Comparison

| Variable | Your .env | .env.example | config.py Default | What to Use in Render |
|----------|-----------|--------------|-------------------|----------------------|
| `MONGODB_URL` | `mongodb+srv://smallikarjun...` | `mongodb+srv://username:password...` | ❌ No default (required) | ✅ Use your actual value |
| `DB_NAME` | `kabaddi` | `sales_automation` | `"sales_automation"` | ✅ Use `kabaddi` |
| `PORT` | `8000` | `8080` | `8000` | ⚠️ Don't set (Render auto-sets) |
| `DEBUG` | `True` | `False` | `False` | ✅ Use `False` |
| `ML_SERVICE_URL` | ❌ Missing | `http://localhost:8080` | `"http://localhost:8080"` | ⚠️ Optional (default is fine) |
| `MAIL_USERNAME` | `mrewards7745@gmail.com` | `your-email@gmail.com` | `""` | ✅ Use your value (if needed) |
| `MAIL_PASSWORD` | `jowo yrvh rvrk hygk` | `your-app-password` | `""` | ✅ Use your value (if needed) |
| `MAIL_FROM` | `mrewards7745@gmail.com` | `your-email@gmail.com` | `""` | ✅ Use your value (if needed) |
| `MAIL_SERVER` | `smtp.gmail.com` | `smtp.gmail.com` | `"smtp.gmail.com"` | ⚠️ Optional (default is fine) |
| `MAIL_PORT` | `587` | `587` | `587` | ⚠️ Optional (default is fine) |

---

## 🔑 Legend

- ✅ **Add to Render** - You should set this
- ⚠️ **Optional** - Has a good default, only change if needed
- ❌ **Don't Set** - Let Render handle it

---

## 🚦 Step-by-Step: Adding to Render

1. Go to your Render service dashboard
2. Click on **"Environment"** tab
3. Click **"Add Environment Variable"**
4. For each variable above marked with ✅:
   - Enter the **Key** (e.g., `MONGODB_URL`)
   - Enter the **Value** (copy from the table above)
   - Click **"Save Changes"**

---

## ❓ Common Questions

**Q: Why is `ML_SERVICE_URL` missing from my `.env`?**  
A: It's optional and has a default value in `config.py`. You only need it if you have a separate ML service.

**Q: Should I change `PORT` in Render?**  
A: No! Render automatically sets `PORT` to whatever it needs. Don't override it.

**Q: What's the difference between `.env` and `.env.example`?**  
A: 
- `.env` = Your **real secrets** (local only, never commit)
- `.env.example` = **Template** with fake values (safe to commit)

**Q: Do I need to add email variables?**  
A: Only if your app needs to send emails. If you're not using email features yet, skip them.

---

## 🎬 What Happens After You Add Variables

1. Render will restart your service
2. Your app will read variables from Render (not from `.env` file)
3. Any variable you didn't set will use the default from `config.py`

---

## 🔒 Security Reminder

> [!CAUTION]
> Make sure `.env` is in your `.gitignore` file! Never commit real credentials to Git.

Check your `.gitignore`:
```bash
cat .gitignore
```

Should contain:
```
.env
```
