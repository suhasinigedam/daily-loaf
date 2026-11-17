What I built: a FastAPI backend with a tested health endpoint, code-quality checks, CI on GitHub, and a protected main.
What I learned: uv, pyproject.toml and uv.lock; the app factory; settings from .env; routers and the /api/v1 prefix; TDD red and green; ruff, mypy, bandit, pip-audit; GitHub Actions; branch rulesets.
What was hard: .env and __pycache__ got committed before .gitignore existed; CI failed on formatting because the formatted files weren’t committed.
What does uv.lock guarantee?
uv.lock pins the exact version of every library, so my Mac, CI and AWS all install the same thing and nothing changes by surprise.”
Why does the health endpoint need no login?
Health is used by monitoring tools that have no login, and it returns no data, so it’s safe to leave public.”