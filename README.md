# 🚀 Job Application Automation System

**Production-Ready Cold Email Outreach for Job Applications**

This system automatically sends personalized job application emails to HR/recruitment teams at 100+ companies. It runs completely on GitHub Actions - just set up ONE secret and you're ready to go!

---

## ✅ What This System Does

| Feature | Description |
|---------|-------------|
| 📧 **Cold Email Outreach** | Sends personalized application emails to verified HR contacts |
| 📋 **100+ Company Emails** | Curated database of HR emails from top Indian & global companies |
| 🔄 **Automatic Follow-ups** | Sends follow-up emails 5 days after initial contact |
| 📎 **Resume Attachment** | Attaches your resume to every email |
| 🚫 **No Duplicates** | Tracks all sent emails, never emails the same person twice |
| ⏰ **3x Daily Automation** | Runs automatically 3 times per day on weekdays (9:30 AM, 2:30 PM, 7:30 PM IST) |
| 🏠 **Work Preference** | Mentions Remote/Hybrid preference while being open to all options |

---

## 🎯 Quick Start (5 Minutes)

### Step 1: Fork This Repository

Click the "Fork" button to create your own copy.

### Step 2: Add Your Gmail App Password

1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add:
   - **Name:** `SENDER_PASSWORD`
   - **Value:** Your Gmail App Password (see below)

### Step 3: Create Gmail App Password

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable **2-Factor Authentication** (required)
3. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
4. Select app: **Mail**, Select device: **Other** (type "GitHub")
5. Copy the 16-character password

### Step 4: Update Your Details

Edit `utils/config.py` with your information:

```python
USER_DETAILS = {
    'full_name': 'Your Name',
    'email': 'your-email@gmail.com',
    'phone': '+91-XXXXXXXXXX',
    'linkedin_url': 'https://linkedin.com/in/your-profile',
    'years_experience': '3',  # Your experience
}
```

### Step 5: Add Your Resume

Replace `resumes/base_resume.pdf` with your resume.

### Step 6: Run the Workflow!

1. Go to **Actions** tab
2. Click **Job Application System (Production Ready)**
3. Click **Run workflow**
4. Select options and click **Run workflow**

---

## 📊 Companies in the Database

The system includes verified HR emails from 100+ companies:

### Indian IT Giants
- Infosys, TCS, Wipro, HCL Tech, Tech Mahindra
- Cognizant, Capgemini, Accenture, Deloitte

### Startups (India)
- Razorpay, Zerodha, Swiggy, Zomato, CRED
- PhonePe, Paytm, Flipkart, Meesho, Groww

### Global Tech Giants
- Google, Microsoft, Amazon, Meta, Apple
- Netflix, Uber, Salesforce, Adobe, Oracle

### Banks & Finance
- HDFC Bank, ICICI Bank, Kotak, Axis Bank
- Bajaj Finance, Yes Bank

### Consulting & Analytics
- McKinsey, BCG, Bain, Fractal Analytics
- Mu Sigma, Tiger Analytics

See full list in `scripts/curated_hr_database.py`

---

## 🔧 Configuration Options

When running the workflow manually:

| Option | Description | Default |
|--------|-------------|---------|
| **Job Location** | Target city for job search | Bangalore |
| **Max Emails** | Maximum new emails to send per run | 15 |
| **Send Follow-ups** | Send follow-up emails to past contacts | true |
| **Scrape Only** | Just scrape jobs, don't send emails | false |
| **Include Portfolio Links** | Add GitHub/Portfolio links in emails | false |
| **Send Slack Notifications** | Slack alerts for interviews/summaries | true |
| **Enable Mobile Alerts** | WhatsApp/Telegram notifications | false |
| **Enable WhatsApp** | WhatsApp via CallMeBot (when mobile alerts on) | false |
| **Enable Telegram** | Telegram Bot notifications | false |
| **Track Email Opens** | Track if HR opened your email | false |
| **Auto-Retry Failed Emails** | Retry bounced emails with alternate addresses | true |

---

## 📱 Feature Setup Guide

### 1. Slack Notifications (Recommended)
Get instant Slack alerts when you receive interview requests or HR replies.

**Setup:**
1. Go to [api.slack.com/apps](https://api.slack.com/apps) → Create New App
2. Choose "From scratch" → Name it "Job Alerts" → Select workspace
3. Go to **Incoming Webhooks** → Enable → **Add New Webhook**
4. Select a channel → Copy the Webhook URL
5. Add secret: `SLACK_WEBHOOK_URL` = your webhook URL

**Enable:** Set `send_slack_notifications` → `true` (default)

---

### 2. WhatsApp Alerts (Optional)
Get instant WhatsApp messages for interviews and daily summaries using free CallMeBot service.

**Is it safe?** ✅ Yes!
- No app installation needed
- Only sends messages TO you (can't read your chats)
- No password shared, just phone number + API key
- Block the number anytime to stop

**Setup:**
1. Save **+34 644 51 95 23** in your contacts as "CallMeBot"
2. Send this WhatsApp message to that number:
   ```
   I allow callmebot to send me messages
   ```
3. You'll receive an API key (save it!)
4. Add secrets in GitHub:
   - `WHATSAPP_PHONE` = Your phone with country code (e.g., `+919876543210`)
   - `CALLMEBOT_API_KEY` = The API key you received

**Enable:** When running workflow:
- Set `enable_mobile_alerts` → `true`
- Set `enable_whatsapp` → `true`

---

### 3. Telegram Alerts (Optional)
Get Telegram notifications for interviews and summaries.

**Setup:**
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow prompts to create your bot
3. Copy the **Bot Token** you receive
4. Message your new bot (just say "hi")
5. Message [@userinfobot](https://t.me/userinfobot) to get your **Chat ID**
6. Add secrets in GitHub:
   - `TELEGRAM_BOT_TOKEN` = Your bot token
   - `TELEGRAM_CHAT_ID` = Your chat ID

**Enable:** When running workflow:
- Set `enable_mobile_alerts` → `true`
- Set `enable_telegram` → `true`

---

### 4. Email Open Tracking (Optional)
Know when HR opens your email (requires your own tracking endpoint).

**How it works:**
- Invisible 1x1 pixel is added to emails
- When HR opens email, pixel loads and logs the open
- You can see open rates and who read your emails

**Setup (Advanced):**
1. Set up a tracking endpoint (Vercel, Netlify, or your server)
2. Add secret: `TRACKING_PIXEL_URL` = Your endpoint URL

**Enable:** Set `enable_open_tracking` → `true`

**Alternative (Simpler):** Use [Mailtrack](https://mailtrack.io/) browser extension for Gmail.

---

### 5. Auto-Retry Failed Emails (Enabled by Default)
Automatically retries bounced emails with verified alternate addresses.

**How it works:**
1. Detects bounced/failed emails
2. Finds alternate HR emails for the same company
3. **Verifies alternates before retry:**
   - DNS MX record check (domain exists)
   - Disposable email detection (rejects temp emails)
   - Corporate domain verification
   - Requires 60+ verification score
4. Retries with verified alternate (max 2 per company)

**Enable:** Set `enable_auto_retry` → `true` (default)

**Disable:** Set `enable_auto_retry` → `false`

---

## 🔐 All Secrets Reference

| Secret Name | Required | Description |
|------------|----------|-------------|
| `SENDER_PASSWORD` | ✅ Yes | Gmail App Password (16 chars) |
| `SLACK_WEBHOOK_URL` | Optional | Slack Incoming Webhook URL |
| `WHATSAPP_PHONE` | Optional | Your phone: `+919876543210` |
| `CALLMEBOT_API_KEY` | Optional | CallMeBot API key |
| `TELEGRAM_BOT_TOKEN` | Optional | Telegram Bot token |
| `TELEGRAM_CHAT_ID` | Optional | Your Telegram chat ID |
| `TRACKING_PIXEL_URL` | Optional | Email open tracking endpoint |

---

## 📁 Project Structure

```
job-automation/
├── .github/workflows/
│   └── apply_jobs.yml          # Main GitHub Actions workflow
├── scripts/
│   ├── curated_hr_database.py  # 100+ verified HR emails
│   ├── reliable_job_scraper.py # Multi-source job scraper
│   ├── email_sender.py         # Personalized email sender
│   ├── followup_sender.py      # Automatic follow-up emails
│   └── email_scraper.py        # Additional email discovery
├── utils/
│   └── config.py               # Your personal details
├── resumes/
│   └── base_resume.pdf         # Your resume
└── data/
    ├── sent_emails_log.csv     # Track of all sent emails
    └── followup_log.csv        # Track of follow-ups
```

---

## 📈 Expected Results

Based on cold email best practices:

| Metric | Expected Range |
|--------|----------------|
| **Emails Sent** | 30-90 per day (3 runs × 30 emails) |
| **Open Rate** | 15-25% |
| **Response Rate** | 5-15% |
| **Interview Calls** | 1-3 per 100 emails |

**Tips for better results:**
- Customize your resume for target roles
- Update `USER_DETAILS` with accurate experience
- Run daily for consistent outreach
- Let follow-ups run automatically

---

## ⚠️ Important Notes

1. **Use responsibly** - Don't spam. The system has built-in rate limiting.
2. **Gmail App Password** - Regular password won't work. Must use App Password.
3. **Email limits** - Gmail allows ~500 emails/day. Stay well under this.
4. **Resume** - Keep PDF under 5MB for reliable attachment.

---

## 🛠️ Troubleshooting

### "Authentication failed" error
- Make sure you're using Gmail App Password, not regular password
- Ensure 2FA is enabled on your Google account

### No emails being sent
- Check if `SENDER_PASSWORD` secret is set correctly
- Look at workflow logs for specific errors

### "No HR emails found" error
- Run the workflow with "Scrape Only" first to populate data

---

## 📝 Adding More Companies

Edit `scripts/curated_hr_database.py`:

```python
{"company": "New Company", "email": "careers@newcompany.com", "type": "general"},
```

---

## ⚖️ Disclaimer

This tool is for personal use only. Users are responsible for:
- Complying with anti-spam laws
- Respecting company policies
- Not exceeding email sending limits
- Using accurate personal information
