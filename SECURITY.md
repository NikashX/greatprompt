# Security Policy

## Reporting a vulnerability

Please **do not** open a public issue for security problems.

Instead, report it privately using GitHub's [private vulnerability reporting](https://github.com/NikashX/greatprompt/security/advisories/new) ("Report a vulnerability" on the Security tab). Include steps to reproduce and the impact you expect.

You can expect an initial response within a few days. Once a fix is ready, we'll publish an advisory and credit you if you'd like.

## Supported versions

Only the latest `main` branch is supported.

## Running your own instance

- Keep your `GEMINI_API_KEY` in `.env` or your host's secret store. Never commit it.
- Keep the rate limits enabled when the app is publicly reachable; they protect your API bill.
- Run behind HTTPS (see the deployment section of the README).
