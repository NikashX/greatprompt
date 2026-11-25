# Contributing to GreatPrompt

Thanks for your interest in improving GreatPrompt! Bug reports, feature ideas, docs fixes, UI polish and system-prompt improvements are all welcome.

## Getting set up

```bash
git clone https://github.com/<your-username>/greatprompt.git
cd greatprompt
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env          # add your own GEMINI_API_KEY
flask --app app run --debug
```

The test suite mocks Gemini, so you don't need an API key to run it:

```bash
pytest
ruff check .
ruff format --check .
```

## Making a change

1. For anything bigger than a small fix, open an issue first so we can agree on the approach.
2. Create a branch from `main`.
3. Keep pull requests focused on one change. Add or update tests when you change behavior.
4. Make sure `pytest` and `ruff check .` pass. CI runs both, and also builds the Docker image.
5. Open a pull request and describe what changed and why. Screenshots help for UI changes.

## Improving the system prompt

Most of the output quality comes from [`prompts.py`](prompts.py). If you change it, please include in your PR a few before/after examples that show the improvement.

## Ground rules

- Never commit secrets. `.env` is git-ignored; use `.env.example` to document new settings.
- Keep the front end dependency-free (plain HTML, CSS and JS) unless there's a strong reason not to.
- Be kind. This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).
