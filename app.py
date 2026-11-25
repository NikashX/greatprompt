import logging
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from google import genai
from google.genai import types
from werkzeug.middleware.proxy_fix import ProxyFix

from prompts import META_PROMPT

load_dotenv()  # no-op in Docker (env comes from compose); handy for local dev

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("greatprompt")


# ---------------- Configuration (secrets come from the environment) ----------------
def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


GEMINI_API_KEY = require_env("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
# The app is free and needs no account, so limits are per visitor IP, plus a
# site-wide daily cap that bounds the Gemini bill even under distributed abuse.
RATE_LIMIT_PER_IP = os.getenv("RATE_LIMIT_PER_IP", "5 per minute; 60 per day")
GLOBAL_DAILY_LIMIT = os.getenv("GLOBAL_DAILY_LIMIT", "3000 per day")
MAX_REQUEST_CHARS = int(os.getenv("MAX_REQUEST_CHARS", "8000"))

gemini = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(
        timeout=60_000,  # ms per attempt; 2 attempts stay under gunicorn's 150s timeout
        retry_options=types.HttpRetryOptions(
            attempts=2, initial_delay=1.0, max_delay=8.0, http_status_codes=[429, 500, 502, 503, 504]
        ),
    ),
)


# ---------------- App ----------------
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.config.update(MAX_CONTENT_LENGTH=64 * 1024)

limiter = Limiter(get_remote_address, app=app, storage_uri=RATELIMIT_STORAGE_URI, default_limits=[])
global_limit = limiter.shared_limit(GLOBAL_DAILY_LIMIT, scope="global", key_func=lambda: "global")


@app.after_request
def security_headers(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if request.is_secure:
        resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return resp


@app.errorhandler(429)
def too_many_requests(_e):
    return jsonify({"error": "You've hit the free usage limit for now. Please try again in a little while."}), 429


# ---------------- Pages ----------------
@app.route("/healthz")
@limiter.exempt
def healthz():
    return {"status": "ok"}


@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/terms")
def terms():
    return render_template("tnc.html")


@app.route("/main")
def main():
    return render_template("main.html", max_chars=MAX_REQUEST_CHARS)


# Accounts were removed; keep old links/bookmarks working.
@app.route("/app")
@app.route("/login")
@app.route("/signup")
@app.route("/resetpass")
@app.route("/verifyOTP")
@app.route("/logout")
def legacy_redirect():
    return redirect(url_for("main"), code=301)


# ---------------- Prompt generation ----------------
OPTIONAL_PARAMS = [
    ("user_tone", "Tone"),
    ("context", "Context"),
    ("prompt_size", "Output Prompt Size"),
    ("negative_aspects", "Negative Aspects"),
    ("country_lang", "Country/Language"),
    ("industry", "Industry"),
    ("output_format", "Output Format"),
]


@app.route("/generate_prompt", methods=["POST"])
@global_limit
@limiter.limit(RATE_LIMIT_PER_IP)
def generate_prompt():
    data = request.get_json(silent=True) or {}
    user_request = str(data.get("user_request") or "").strip()
    if not user_request:
        return jsonify({"error": "Please describe what you want a prompt for."}), 400

    parts = [f"User Request: {user_request}"]
    extras = [f"{label}: {str(data.get(key)).strip()}" for key, label in OPTIONAL_PARAMS if data.get(key)]
    if extras:
        parts.append("Optional Parameters By User\n" + "\n".join(extras))
    contents = "\n\n".join(parts)
    if len(contents) > MAX_REQUEST_CHARS:
        return jsonify({"error": f"Request is too long (max {MAX_REQUEST_CHARS} characters)."}), 400

    try:
        response = gemini.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=META_PROMPT),
        )
        output = response.text
    except Exception:
        log.exception("Gemini request failed")
        return jsonify({"error": "Couldn't generate a prompt right now. Please try again in a moment."}), 502

    if not output:
        return jsonify({"error": "The model returned an empty response. Try rephrasing your request."}), 502

    log.info("Generated prompt (%d input chars)", len(contents))
    return jsonify({"generated_output": output})


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
