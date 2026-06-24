from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path


WINDOWS_CHROME_PATHS = (
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
)


def parse_major_version(version_text: str | None) -> int | None:
    if not version_text:
        return None
    match = re.search(r"\b(\d+)(?:\.\d+)+\b", version_text)
    return int(match.group(1)) if match else None


def major_versions_match(driver_version: str | None, chrome_version: str | None) -> bool:
    driver_major = parse_major_version(driver_version)
    chrome_major = parse_major_version(chrome_version)
    return driver_major is not None and chrome_major is not None and driver_major == chrome_major


def ensure_matching_major_versions(driver_version: str | None, chrome_version: str | None) -> None:
    driver_major = parse_major_version(driver_version)
    chrome_major = parse_major_version(chrome_version)
    if driver_major is None or chrome_major is None or driver_major == chrome_major:
        return

    raise RuntimeError(
        f"ChromeDriver {driver_major} does not match Chrome {chrome_major}. "
        "Use the matching ChromeDriver version or enable automatic project download."
    )


def get_command_version(command: str | Path) -> str | None:
    try:
        result = subprocess.run(
            [str(command), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return (result.stdout or result.stderr).strip() or None


def find_chrome_binary() -> Path | str:
    for path in WINDOWS_CHROME_PATHS:
        if path.exists():
            return path

    path_value = shutil.which("chrome") or shutil.which("google-chrome") or shutil.which("chromium")
    if path_value:
        return path_value

    raise RuntimeError("Chrome executable was not found. Install Chrome or add it to PATH.")


def get_chrome_version(chrome_binary: str | Path | None = None) -> str:
    binary = chrome_binary or find_chrome_binary()
    version = get_command_version(binary)
    if not parse_major_version(version):
        version = get_chrome_version_from_install_dir(binary)
    if not parse_major_version(version):
        raise RuntimeError(f"Unable to read Chrome version from {binary}")
    return version


def get_chromedriver_version(chromedriver_path: str | Path) -> str | None:
    return get_command_version(chromedriver_path)


def get_chrome_version_from_install_dir(chrome_binary: str | Path) -> str | None:
    binary = Path(chrome_binary)
    if not binary.exists():
        return None

    versions = []
    for child in binary.parent.iterdir():
        if child.is_dir() and parse_major_version(child.name) is not None:
            versions.append(child.name)

    if not versions:
        return None
    return sorted(versions, key=_version_sort_key, reverse=True)[0]


def _version_sort_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split(".") if part.isdigit())
