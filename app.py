"""URL ➜ HTML API (Flask).

Auth: send your key in the `X-API-Key` header (or `?key=`).

  GET  /health                      no auth — uptime / queue stats
  GET  /api/html?url=               page HTML as JSON (add &raw=1 for plain HTML)
  GET  /api/seo?url=                SEO report JSON
  GET  /api/tech?url=               tech-stack JSON
  POST /api/jobs   {"url","type"}   type = "site" (full crawl) | "zip" (single page)
  GET  /api/jobs/<id>               status / progress / result
  GET  /api/jobs/<id>/download      the ZIP once status == "done"
"""

import hmac
import time
from functools import wraps

import requests
from flask import Flask, Response, jsonify, request, send_file

import config
import core
import jobs

app = Flask(__name__)
START_TIME = time.time()


def _error(message, status):
    return jsonify({"ok": False, "error": message}), status


def _client_key():
    supplied = request.headers.get("X-API-Key") or request.args.get("key") or ""
    for valid in config.API_KEYS:
        if supplied and hmac.compare_digest(supplied, valid):
            return valid
    return None


def require_key(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        key = _client_key()
        if not key:
            return _error("Invalid or missing API key.", 401)
        request.api_key = key
        return fn(*args, **kwargs)
    return wrapper


def _get_url_arg(source):
    url = (source.get("url") or "").strip()
    if not core.is_valid_url(url):
        return None
    return url


def _handle_fetch_errors(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except core.UnsafeURL as e:
            return _error(str(e), 400)
        except core.ResponseTooLarge as e:
            return _error(str(e), 413)
        except requests.exceptions.Timeout:
            return _error("The target site timed out.", 504)
        except requests.exceptions.RequestException as e:
            return _error(f"Could not fetch the URL: {str(e)[:200]}", 502)
    return wrapper


@app.get("/")
def index():
    return jsonify({"name": "URL to HTML API", "docs": "see README", "health": "/health"})


@app.get("/health")
def health():
    up = int(time.time() - START_TIME)
    return jsonify({"status": "ok", "uptime_seconds": up, "jobs": jobs.stats()})


@app.get("/api/html")
@require_key
@_handle_fetch_errors
def api_html():
    url = _get_url_arg(request.args)
    if not url:
        return _error("Send a valid http(s) URL in ?url=", 400)
    data = core.fetch_html(url)
    if request.args.get("raw") == "1":
        return Response(
            data["html"], mimetype="text/html",
            headers={"X-Upstream-Status": str(data["status"])},
        )
    return jsonify({"ok": True, **data})


@app.get("/api/seo")
@require_key
@_handle_fetch_errors
def api_seo():
    url = _get_url_arg(request.args)
    if not url:
        return _error("Send a valid http(s) URL in ?url=", 400)
    return jsonify({"ok": True, **core.seo_report(url)})


@app.get("/api/tech")
@require_key
@_handle_fetch_errors
def api_tech():
    url = _get_url_arg(request.args)
    if not url:
        return _error("Send a valid http(s) URL in ?url=", 400)
    return jsonify({"ok": True, **core.tech_report(url)})


@app.post("/api/jobs")
@require_key
def api_job_create():
    body = request.get_json(silent=True) or {}
    url = _get_url_arg(body)
    if not url:
        return _error('Send JSON like {"url": "https://example.com", "type": "site"}', 400)
    kind = (body.get("type") or "site").lower()
    if kind not in ("site", "zip"):
        return _error('type must be "site" or "zip".', 400)
    try:
        core._validated_public_url(url)  # fail fast, before queueing
    except core.UnsafeURL as e:
        return _error(str(e), 400)
    try:
        view = jobs.submit(request.api_key, kind, url)
    except jobs.QueueFull:
        return _error("Server queue is full — try again in a minute.", 429)
    return jsonify({"ok": True, **view}), 202


@app.get("/api/jobs/<job_id>")
@require_key
def api_job_status(job_id):
    view = jobs.get(job_id, request.api_key)
    if not view:
        return _error("Job not found or expired.", 404)
    return jsonify({"ok": True, **view})


@app.get("/api/jobs/<job_id>/download")
@require_key
def api_job_download(job_id):
    found = jobs.file_for(job_id, request.api_key)
    if not found:
        return _error("Result not ready, failed, or expired.", 404)
    path, filename = found
    return send_file(path, mimetype="application/zip", as_attachment=True, download_name=filename)


if __name__ == "__main__":
    # Dev / Termux. In production use gunicorn (see README).
    app.run(host="0.0.0.0", port=config.PORT, threaded=True)
