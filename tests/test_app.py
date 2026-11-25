import pytest


@pytest.mark.parametrize("path", ["/", "/main", "/terms", "/healthz"])
def test_pages_load(client, path):
    assert client.get(path).status_code == 200


@pytest.mark.parametrize("path", ["/login", "/signup", "/resetpass", "/verifyOTP", "/logout", "/app"])
def test_legacy_auth_urls_redirect_to_builder(client, path):
    resp = client.get(path)
    assert resp.status_code == 301
    assert resp.headers["Location"].endswith("/main")


def test_security_headers(client):
    resp = client.get("/")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"


def test_generate_returns_model_output(client, fake_gemini):
    resp = client.post("/generate_prompt", json={"user_request": "A launch email"})
    assert resp.status_code == 200
    assert resp.get_json()["generated_output"] == fake_gemini.response_text


def test_generate_includes_optional_params_with_correct_labels(client, fake_gemini):
    client.post(
        "/generate_prompt",
        json={"user_request": "A launch email", "context": "B2B SaaS", "prompt_size": "short", "user_tone": ""},
    )
    contents = fake_gemini.calls[0]["contents"]
    assert "User Request: A launch email" in contents
    assert "Context: B2B SaaS" in contents
    assert "Output Prompt Size: short" in contents
    assert "Tone:" not in contents  # empty fields are skipped


def test_generate_requires_request_text(client, fake_gemini):
    resp = client.post("/generate_prompt", json={"user_request": "   "})
    assert resp.status_code == 400
    assert fake_gemini.calls == []


def test_generate_rejects_overlong_request(client, fake_gemini):
    resp = client.post("/generate_prompt", json={"user_request": "x" * 9000})
    assert resp.status_code == 400
    assert fake_gemini.calls == []


def test_generate_handles_invalid_json(client, fake_gemini):
    resp = client.post("/generate_prompt", data="not json", content_type="application/json")
    assert resp.status_code == 400


def test_generate_hides_upstream_errors(client, fake_gemini):
    fake_gemini.error = RuntimeError("secret upstream detail")
    resp = client.post("/generate_prompt", json={"user_request": "hi"})
    assert resp.status_code == 502
    assert "secret upstream detail" not in resp.get_data(as_text=True)


def test_generate_handles_empty_model_response(client, fake_gemini):
    fake_gemini.response_text = ""
    resp = client.post("/generate_prompt", json={"user_request": "hi"})
    assert resp.status_code == 502


def test_per_ip_rate_limit(client, fake_gemini):
    statuses = [client.post("/generate_prompt", json={"user_request": "hi"}).status_code for _ in range(6)]
    assert statuses[:5] == [200] * 5
    assert statuses[5] == 429
    assert "error" in client.post("/generate_prompt", json={"user_request": "hi"}).get_json()
