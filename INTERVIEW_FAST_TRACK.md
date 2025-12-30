# ⚡ FAST TRACK TO INTERVIEWS - QUICK START GUIDE

**Goal: Maximum interview calls in minimum time**

---

## 🚀 STEP 1: Set Up GitHub Secrets (REQUIRED)

Go to your GitHub repo → Settings → Secrets and variables → Actions → New repository secret

### Required Secrets:
```
GMAIL_USER          = your.email@gmail.com
GMAIL_APP_PASSWORD  = xxxx xxxx xxxx xxxx   (Get from Google App Passwords)
```

### Personal Info (for emails):
```
APPLICANT_NAME      = Ajay Dhage
APPLICANT_EMAIL     = your.email@gmail.com
APPLICANT_PHONE     = +91 98XXXXXXXX
APPLICANT_LINKEDIN  = https://linkedin.com/in/yourprofile
YEARS_EXPERIENCE    = 5
APPLICANT_SKILLS    = Python, JavaScript, React, Node.js, AWS
APPLICANT_TARGET_ROLE = Full Stack Developer
```

### AI Keys (for smart emails - FREE!):
```
GROQ_API_KEY        = gsk_xxx (get free at console.groq.com)
OPENROUTER_API_KEY  = sk-or-xxx (get free at openrouter.ai)
```

---

## 🚀 STEP 2: Add Your Resume

1. Upload your resume to: `resumes/resume.pdf`
2. Or update the `RESUME_PATH` in the workflow

---

## 🚀 STEP 3: Run the Workflow!

### Option A: Manual Run (Immediate)
1. Go to GitHub repo → Actions tab
2. Click "⚡ Fast Track to Interviews"
3. Click "Run workflow"
4. Choose max applications (default: 30)
5. Click "Run workflow" button

### Option B: Automatic (Every 3 hours)
The workflow runs automatically:
- Monday-Friday
- At 6am, 9am, 12pm, 3pm, 6pm
- Sends up to 30 applications each run

---

## 📊 What It Does:

```
Phase 1: SCRAPE (15+ sources)
├── RemoteOK API
├── Arbeitnow API  
├── Adzuna API
├── Google Jobs
├── Naukri.com
├── LinkedIn
├── Indeed
├── Glassdoor
└── ... and more!

Phase 2: FIND HR EMAILS
├── Curated database (100+ verified)
├── Advanced discovery
├── Email pattern generation
└── Web scraping

Phase 3: SEND APPLICATIONS
├── AI-generated personalized emails
├── Attach resume automatically
├── Log all applications
└── Rate-limited (won't get flagged)

Phase 4: FOLLOW-UPS
├── Auto follow-up after 3 days
├── Smart personalization
└── Track responses

Phase 5: NOTIFY YOU
├── Slack notifications
├── Mobile alerts
└── Summary report
```

---

## 🎯 Expected Results:

| Timeframe | Applications | Expected Callbacks |
|-----------|-------------|-------------------|
| Day 1     | 30-50       | 1-3 responses     |
| Week 1    | 150-300     | 5-15 interviews   |
| Month 1   | 500-1000    | 20-50 interviews  |

---

## 📱 Get Notified Instantly (Optional)

### Slack Notifications:
1. Create Slack webhook: api.slack.com/messaging/webhooks
2. Add secret: `SLACK_WEBHOOK_URL`

### Mobile Push (Pushover):
1. Get Pushover app: pushover.net
2. Add secrets: `PUSHOVER_USER_KEY`, `PUSHOVER_API_TOKEN`

---

## 🔧 Customize for Your Profile:

### Edit Target Companies
File: `scripts/curated_hr_database.py`
- Add more HR emails
- Add target companies

### Edit Email Templates
File: `scripts/max_applications_sender.py`
- Modify `generate_email_body()` method

### Edit Job Search Criteria
File: `scripts/bulletproof_job_engine.py`
- Update `target_roles` list
- Update `locations` list

---

## 💡 Pro Tips:

1. **Run manually first** to test before automation
2. **Start with 10-20 applications** to test email deliverability
3. **Check spam folder** - first few emails might land there
4. **Update resume** for different roles (tailored versions)
5. **Reply quickly** when you get responses!

---

## 🆘 Troubleshooting:

### "No emails sent"
- Check `GMAIL_APP_PASSWORD` is correct (not your regular password)
- Enable "Less secure apps" or use App Password

### "Emails going to spam"
- Reduce sending rate (increase delay)
- Use professional email content
- Enable email authentication (SPF/DKIM)

### "No jobs found"
- Check internet connectivity
- API sources might be temporarily down
- Try manual run

---

## 🎉 Good Luck!

Remember: Getting a job is a numbers game. More applications = More interviews = Better offers!

Keep the automation running and focus on preparing for interviews!
