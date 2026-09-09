# Contributing

Thanks for helping improve this project.

## Local Setup

```powershell
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill `.env` locally. Never commit `.env`, API keys, cookies, screenshots, or ChromeDriver binaries.

## Checks

Run these before opening a pull request:

```powershell
python -m pytest tests -q
python -m compileall -q utils tests scripts batch_homework.py finish_work.py xuexitong.py
```

## Pull Requests

- Keep changes focused.
- Add or update tests for behavior changes.
- Do not include generated files such as `__pycache__/`, `.drivers/`, screenshots, or IDE folders.
- Remove private URLs and personal information from logs before posting them.
