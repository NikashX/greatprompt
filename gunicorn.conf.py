import os

bind = "0.0.0.0:8000"
# Single worker + threads: Gemini calls are I/O-bound, and the in-memory rate
# limiter stays accurate (it is per-process).
workers = 1
worker_class = "gthread"
threads = int(os.getenv("GUNICORN_THREADS", "8"))
timeout = 150  # Gemini responses can take a while
graceful_timeout = 30
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()
forwarded_allow_ips = "*"  # container is only reachable via the reverse proxy
