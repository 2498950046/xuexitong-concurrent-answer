from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.chromedriver_manager import ensure_project_chromedriver  # noqa: E402
from utils.config import AppConfig  # noqa: E402


def main() -> int:
    config = AppConfig.from_env()
    path = ensure_project_chromedriver(config.chromedriver_path, project_root=PROJECT_ROOT)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
