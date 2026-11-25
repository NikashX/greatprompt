# GreatPrompt

**Turn a rough idea into a precise, expert-level prompt for any AI model.**

GreatPrompt is a free, open-source prompt generator. Describe what you want in plain words, optionally fine-tune tone, audience, length, region, industry and output format, and get back:

1. the assumptions it made about your request,
2. a structured, ready-to-paste prompt (role, context, instructions, constraints), and
3. recommended model settings (temperature, top-p, max tokens).

The generated prompts work in ChatGPT, Claude, Gemini and other LLMs. No account or sign-up needed.

## Features

- **One-box prompt builder**: type an idea, press ⌘/Ctrl + Enter, copy the result.
- **Optional fine-tuning**: tone, context, prompt size, things to avoid, language/region, industry, output format.
- **Formatted output** with one-click copy for the prompt block.
- **Abuse protection** for public hosting: a per-IP rate limit plus a site-wide daily cap on generations.
- **Production-ready Docker setup**: gunicorn, non-root, read-only filesystem, health check.

## Tech stack

Python · Flask · Google Gemini (`google-genai`) · gunicorn · Docker. Plain HTML/CSS/JS front end, no build step.

## Quick start

You need a Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).

### With Docker (recommended)

```bash
git clone https://github.com/NikashX/greatprompt.git
cd greatprompt
cp .env.example .env        # then set GEMINI_API_KEY
docker compose up -d --build
```

Open http://localhost:8000.

### Without Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then set GEMINI_API_KEY
flask --app app run --debug
```

Open http://localhost:5000.

## Configuration

All configuration is via environment variables (or `.env`, which is git-ignored and never committed).

| Variable | Required | Default | Notes |
|---|---|---|---|
| `GEMINI_API_KEY` | yes | | Your Google AI Studio key |
| `GEMINI_MODEL` | no | `gemini-3.5-flash` | Any Gemini model your key can use |
| `RATE_LIMIT_PER_IP` | no | `5 per minute; 60 per day` | [Flask-Limiter syntax](https://flask-limiter.readthedocs.io/en/stable/configuration.html#rate-limit-string-notation) |
| `GLOBAL_DAILY_LIMIT` | no | `3000 per day` | Site-wide cap that bounds your Gemini bill |
| `RATELIMIT_STORAGE_URI` | no | `memory://` | Use `redis://…` if you run more than one process |
| `MAX_REQUEST_CHARS` | no | `8000` | Max size of a single request |
| `APP_PORT` | no | `8000` | Host port for Docker Compose |
| `GUNICORN_THREADS` | no | `8` | Worker threads |
| `LOG_LEVEL` | no | `INFO` | |

## Deploying

The Compose file publishes the app on `127.0.0.1:${APP_PORT}` only, so put a reverse proxy with HTTPS in front of it. Example nginx site:

```nginx
server {
    server_name prompts.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_read_timeout 150s;   # prompt generation can take a while
    }
}
```

Then run `sudo certbot --nginx -d prompts.example.com` for HTTPS.

If your reverse proxy also runs in Docker, `127.0.0.1` inside it is not the host. Either attach both containers to a shared Docker network and proxy to `http://greatprompt:8000`, or remove the `127.0.0.1:` prefix in `docker-compose.yml` and firewall the port.

Update with `git pull && docker compose up -d --build`. View logs with `docker compose logs -f`.

## How it works

The app sends your request, plus any fine-tuning fields, to Gemini along with a detailed system prompt (the "Prompt Architect" instructions in [`prompts.py`](prompts.py)). Improving that system prompt is the easiest way to improve the output, and contributions to it are welcome.

```
app.py            Flask routes, rate limiting, Gemini client
prompts.py        The system prompt
templates/        Landing page, prompt builder, terms
static/css/       Shared styles
tests/            pytest suite (Gemini is mocked)
```

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) to get set up, and please follow the [Code of Conduct](CODE_OF_CONDUCT.md). To report a security issue, see [SECURITY.md](SECURITY.md); please don't open a public issue for it.

## License

[MIT](LICENSE)
