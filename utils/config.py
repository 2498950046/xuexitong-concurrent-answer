from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Mapping


DEFAULT_LOGIN_URL = "https://passport2.chaoxing.com/login"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-pro"
DEFAULT_BATCH_SIZE = 20
DEFAULT_WORKER_COUNT = 4
DEFAULT_DOTENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def _get_int(env: Mapping[str, str], name: str, default: int) -> int:
    value = env.get(name)
    if value is None or value.strip() == "":
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be greater than 0")
    return parsed


@dataclass(frozen=True)
class AppConfig:
    login_url: str = DEFAULT_LOGIN_URL
    phone: str | None = None
    password: str | None = None
    chromedriver_path: str | None = None
    deepseek_api_key: str | None = None
    deepseek_base_url: str = DEFAULT_DEEPSEEK_BASE_URL
    deepseek_model: str = DEFAULT_DEEPSEEK_MODEL
    batch_size: int = DEFAULT_BATCH_SIZE
    worker_count: int = DEFAULT_WORKER_COUNT
    browser_detach: bool = True
    work_url: str | None = None

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        dotenv_path: str | Path | None = DEFAULT_DOTENV_PATH,
    ) -> "AppConfig":
        source = _merge_dotenv_and_env(os.environ if env is None else env, dotenv_path)
        return cls(
            login_url=source.get("XUEXITONG_LOGIN_URL", DEFAULT_LOGIN_URL),
            phone=source.get("XUEXITONG_PHONE") or None,
            password=source.get("XUEXITONG_PASSWORD") or None,
            chromedriver_path=source.get("XUEXITONG_CHROMEDRIVER") or None,
            deepseek_api_key=source.get("DEEPSEEK_API_KEY") or None,
            deepseek_base_url=source.get("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL),
            deepseek_model=source.get("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL),
            batch_size=_get_int(source, "XUEXITONG_BATCH_SIZE", DEFAULT_BATCH_SIZE),
            worker_count=_get_int(source, "XUEXITONG_WORKER_COUNT", DEFAULT_WORKER_COUNT),
            browser_detach=source.get("XUEXITONG_BROWSER_DETACH", "1").lower()
            not in {"0", "false", "no"},
            work_url=source.get("XUEXITONG_WORK_URL") or None,
        )

    def require_login(self) -> tuple[str, str]:
        missing = []
        if not self.phone:
            missing.append("XUEXITONG_PHONE")
        if not self.password:
            missing.append("XUEXITONG_PASSWORD")
        if missing:
            raise ValueError("Missing login environment variables: " + ", ".join(missing))
        return self.phone, self.password

    def require_deepseek_api_key(self) -> str:
        if not self.deepseek_api_key:
            raise ValueError("Missing DEEPSEEK_API_KEY environment variable")
        return self.deepseek_api_key

    def require_existing_chromedriver(self) -> str | None:
        if not self.chromedriver_path:
            return None

        path = Path(self.chromedriver_path)
        if not path.exists():
            raise FileNotFoundError(
                f"XUEXITONG_CHROMEDRIVER points to a missing file: {self.chromedriver_path}"
            )
        return str(path)


def _merge_dotenv_and_env(
    env: Mapping[str, str],
    dotenv_path: str | Path | None,
) -> dict[str, str]:
    merged = _read_dotenv(dotenv_path)
    merged.update(env)
    return merged


def _read_dotenv(dotenv_path: str | Path | None) -> dict[str, str]:
    if dotenv_path is None:
        return {}

    path = Path(dotenv_path)
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        values[key] = _strip_quotes(value.strip())
    return values


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
