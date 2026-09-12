# Pulse - Crypto Trading Intelligence

Static morning dashboard for crypto market intelligence.

The production site is static-only. GitHub Actions runs the Python agent, commits `data/latest-report.json`, copies it to `frontend/data/latest-report.json`, and Netlify serves that JSON at `/data/latest-report.json`.

## Setup

From the project root:

```bash
py -3 -m pip install -r requirements.txt
copy .env.example .env
```

Fill in any local keys in `.env`. `GROQ_API_KEY` enables the AI briefing, `CMC_API_KEY` enables CoinMarketCap data, and `TELEGRAM_BOT_TOKEN` plus `TELEGRAM_CHAT_ID` enable push notifications.

## Run The Agent

Generate or refresh the static report:

```bash
py -3 agent/run.py
```

This writes `data/latest-report.json` and `frontend/data/latest-report.json`.

## Local Dev With Live API

Use the local server when you want `/api/report` and `/api/health` for development or testing:

```bash
py -3 serve.py
```

Open http://127.0.0.1:8080

These API routes are local-only. They do not run on Netlify.

## Production

Production is static hosting only:

1. GitHub Actions runs `agent/run.py` on the daily schedule or manual dispatch.
2. The workflow writes `data/latest-report.json`.
3. The workflow saves a dated copy to `data/history/YYYY-MM-DD.json`.
4. The workflow copies the latest report to `frontend/data/latest-report.json`.
5. Netlify publishes the `frontend` folder and the app reads `/data/latest-report.json`.

Add these GitHub Actions secrets for production runs:

- `GROQ_API_KEY`
- `CMC_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
