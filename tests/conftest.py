import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

# The app reads config at import time; give it a dummy key so no real one is needed.
os.environ.setdefault("GEMINI_API_KEY", "test-key")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app as app_module  # noqa: E402


class FakeModels:
    def __init__(self):
        self.calls = []
        self.response_text = "Assumptions...\n\n```\nYou are an expert.\n```"
        self.error = None

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(text=self.response_text)


@pytest.fixture
def fake_gemini(monkeypatch):
    models = FakeModels()
    monkeypatch.setattr(app_module, "gemini", SimpleNamespace(models=models))
    return models


@pytest.fixture
def client():
    app_module.app.config.update(TESTING=True)
    app_module.limiter.reset()
    with app_module.app.test_client() as c:
        yield c
