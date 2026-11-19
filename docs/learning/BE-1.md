What I built: a FastAPI backend with a tested health endpoint, code-quality checks, CI on GitHub, and a protected main.
What I learned: uv, pyproject.toml and uv.lock; the app factory; settings from .env; routers and the /api/v1 prefix; TDD red and green; ruff, mypy, bandit, pip-audit; GitHub Actions; branch rulesets.
What was hard: .env and __pycache__ got committed before .gitignore existed; CI failed on formatting because the formatted files weren’t committed.
What does uv.lock guarantee?
uv.lock pins the exact version of every library, so my Mac, CI and AWS all install the same thing and nothing changes by surprise.”
Why does the health endpoint need no login?
Health is used by monitoring tools that have no login, and it returns no data, so it’s safe to leave public.”

1. What does your CI pipeline check, and why does each check matter?

“On every pull request, GitHub Actions installs the exact dependencies from the lock file and runs six checks. Ruff lints and checks formatting, so the code stays consistent and simple bugs like unused imports are caught. Mypy in strict mode checks the type hints, so type errors appear before runtime. Pytest runs the tests with coverage, which proves behaviour still works. Bandit scans my code for insecure patterns, and pip-audit checks my dependencies for known vulnerabilities. A separate gitleaks job scans the whole history for leaked secrets. main is protected, so nothing merges unless all of this is green.”

The point to get across: CI is the same set of checks for everyone, every time. It caught your formatting mistake that your Mac didn’t.

2. Why do you build the app with a factory function?

“create_app() builds and returns the FastAPI app instead of creating it when the module is imported. That gives me control over its dependencies: tests pass in fake settings, and later a fake token verifier and fake S3, without touching real configuration or AWS. Production calls the same function with real settings. It’s dependency injection at the application level, and it keeps tests isolated and fast.”

The point to get across: testability. The same code runs with different settings and dependencies.

3. What’s the difference between pyproject.toml and uv.lock?

“pyproject.toml is what I ask for: the project’s metadata, the direct dependencies, often with loose version ranges, and tool settings like ruff and pytest. I edit it, or uv edits it when I run uv add. uv.lock is what I get: the exact resolved version of every package, including indirect ones, with hashes. It’s generated, never edited by hand, and committed, so my laptop, CI and production install identical environments. CI uses uv sync --locked, which fails if the two files are out of sync.”