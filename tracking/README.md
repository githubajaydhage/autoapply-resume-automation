# 📧 Email Open Tracking Setup

This guide helps you set up **free email open tracking** using Cloudflare Workers.

## 🚀 Quick Setup (10 minutes)

### Step 1: Create Cloudflare Account (Free)

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com)
2. Sign up (no credit card required)
3. Verify your email

### Step 2: Create a Worker

1. In Cloudflare dashboard, click **Workers & Pages** (left sidebar)
2. Click **Create Application** → **Create Worker**
3. Name it: `email-tracker`
4. Click **Deploy**

### Step 3: Add the Tracking Code

1. Click **Edit Code** on your new worker
2. Delete all existing code
3. Copy-paste the code from `worker.js` file in this folder
4. Click **Save and Deploy**

### Step 4: Get Your Tracking URL

Your tracking URL will be:
```
https://email-tracker.<your-subdomain>.workers.dev/track
```

Example: `https://email-tracker.ajay123.workers.dev/track`

### Step 5: Add to GitHub Secrets

1. Go to your GitHub repo → Settings → Secrets → Actions
2. Add new secret:
   - **Name:** `TRACKING_PIXEL_URL`
   - **Value:** `https://email-tracker.<your-subdomain>.workers.dev/track`

---

## ✅ Done!

Now when you run the workflow:
1. Each email gets a unique tracking ID
2. Invisible pixel is embedded in emails
3. When HR opens email, Cloudflare logs it
4. View logs in Cloudflare Workers dashboard!

---

## 📊 Viewing Open Statistics

### Option 1: Cloudflare Dashboard
1. Go to Workers & Pages → email-tracker
2. Click **Logs** tab
3. See real-time opens with tracking IDs

### Option 2: KV Storage (Permanent Logs)
The worker stores opens in Cloudflare KV (free tier: 100k reads/day).

To view stored data:
1. Go to Workers & Pages → KV
2. Click on `EMAIL_OPENS` namespace
3. Browse all recorded opens

---

## 🔧 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    EMAIL OPEN TRACKING                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Workflow runs                                            │
│     ↓                                                        │
│  2. Email sent with hidden pixel:                            │
│     <img src="https://your-worker.dev/track?tid=abc123">    │
│     ↓                                                        │
│  3. HR opens email                                           │
│     ↓                                                        │
│  4. Email client loads pixel image                           │
│     ↓                                                        │
│  5. Cloudflare Worker receives request                       │
│     - Logs: tracking_id, timestamp, user_agent, IP           │
│     - Stores in KV database                                  │
│     - Returns 1x1 transparent GIF                            │
│     ↓                                                        │
│  6. You check Cloudflare dashboard to see opens!             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚠️ Limitations

1. **Image blocking**: Some email clients block images by default
2. **Privacy tools**: Recipients with privacy extensions won't trigger
3. **Multiple opens**: Same person opening multiple times counts multiple times

**Typical detection rate:** 40-60% of actual opens are tracked.

---

## 🆓 Cloudflare Free Tier Limits

- **100,000 requests/day** - More than enough for email tracking
- **10ms CPU time** - Our script uses <1ms
- **KV Storage**: 100k reads, 1k writes per day

You'll never hit these limits with normal job application volumes!
