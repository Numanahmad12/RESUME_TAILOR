# Deployment Guide

## GitHub

```bash
# One-time: create the repo on github.com first (e.g. "ResumeAI")
git remote add origin https://github.com/<your-username>/ResumeAI.git
git branch -M main
git push -u origin main
```

If GitHub asks for credentials, use a **Personal Access Token** (Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token, scope: `repo`). Paste it as the password when prompted.

## Vercel

The simplest path: import the GitHub repo into Vercel.

1. Go to https://vercel.com/new
2. Click "Import Git Repository" → select your GitHub repo
3. Vercel auto-detects Next.js. The `vercel.json` at the repo root sets:
   - Build command: `cd frontend && npm install && npm run build`
   - Output directory: `frontend/.next`
4. Click **Deploy**

The `/api/*` rewrite in `frontend/next.config.js` proxies to `http://localhost:8000`, which only works locally. For production, you have two options:

- **A. Vercel Functions** (simplest): the `frontend/src/pages/api/*` routes already exist as Next.js API routes. They call the FastAPI backend via `fetch`. Update the `fetch` calls to use the production backend URL.
- **B. Separate backend host**: deploy the FastAPI backend to Railway, Render, or Fly.io, then set the rewrite destination in `vercel.json` to that URL.

For now, the app works in **static-only mode** (no backend) for the landing page. The `/tool` page requires the backend.
