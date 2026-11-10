# URL ➜ HTML API

Run locally / Termux:  `pip install -r requirements.txt && python app.py`
Production (Render):   push this folder to GitHub → New Web Service (or use render.yaml)
Start command:         `gunicorn app:app --workers 1 --threads 32 --timeout 120 --bind 0.0.0.0:$PORT`
(keep `--workers 1`: job state is in memory)

API key: `config.py` → `API_KEYS`. Send as header `X-API-Key`.

## Endpoints
| Method | Path | Purpose |
|---|---|---|
| GET | /health | uptime + job counts (no key) |
| GET | /api/html?url=…[&raw=1] | page HTML |
| GET | /api/seo?url=… | SEO report |
| GET | /api/tech?url=… | tech stack |
| POST | /api/jobs `{"url","type":"site"\|"zip"}` | start crawl / single-page ZIP → 202 + job_id |
| GET | /api/jobs/<id> | status: queued / running / done / failed |
| GET | /api/jobs/<id>/download | ZIP when done |

## Example
```
curl -H "X-API-Key: KEY" -X POST https://HOST/api/jobs \
     -H "Content-Type: application/json" -d '{"url":"https://example.com","type":"site"}'
curl -H "X-API-Key: KEY" https://HOST/api/jobs/JOB_ID
curl -H "X-API-Key: KEY" -o site.zip https://HOST/api/jobs/JOB_ID/download
```
