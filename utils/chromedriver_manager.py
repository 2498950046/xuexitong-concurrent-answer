from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import platform
import shutil
import urllib.request
import zipfile

from utils.browser_versions import (
    get_chrome_version,
    get_chromedriver_version,
    major_versions_match,
    parse_major_version,
)


CHROME_FOR_TESTING_MILESTONES_URL = (
    "https://googlechromelabs.github.io/chrome-for-testing/"
    "latest-versions-per-milestone-with-downloads.json"
)
DRIVER_DIR_NAME = ".drivers"


@dataclass(frozen=True)
class DriverDownload:
    version: str
    url: str


def project_driver_path(project_root: str | Path | None = None) -> Path:
    root = Path(project_root) if project_root else Path(__file__).resolve().parent.parent
    executable_name = "chromedriver.exe" if platform.system().lower() == "windows" else "chromedriver"
    return root / DRIVER_DIR_NAME / executable_name


def ensure_project_chromedriver(
    configured_path: str | Path | None = None,
    project_root: str | Path | None = None,
    force_refresh: bool = False,
) -> str:
    chrome_version = get_chrome_version()
    chrome_major = parse_major_version(chrome_version)
    if chrome_major is None:
        raise RuntimeError(f"Unable to parse Chrome version: {chrome_version}")

    configured = Path(configured_path) if configured_path else None
    if configured and configured.exists() and not force_refresh:
        configured_version = get_chromedriver_version(configured)
        if major_versions_match(configured_version, chrome_version):
            print(f"ChromeDriver 已匹配 Chrome {chrome_major}: {configured}", flush=True)
            return str(configured)
        print(
            f"已配置的 ChromeDriver 不匹配当前 Chrome {chrome_major}，将下载项目内匹配版本。",
            flush=True,
        )

    target_path = project_driver_path(project_root)
    existing_version = get_chromedriver_version(target_path) if target_path.exists() else None
    if major_versions_match(existing_version, chrome_version) and not force_refresh:
        print(f"项目内 ChromeDriver 已匹配 Chrome {chrome_major}: {target_path}", flush=True)
        return str(target_path)

    action = "刷新" if force_refresh else "下载"
    print(f"正在{action} Chrome {chrome_major} 对应的 ChromeDriver 到项目目录...", flush=True)
    metadata = fetch_driver_metadata()
    download = choose_chromedriver_download(metadata, chrome_major, current_platform_name())
    download_and_extract_chromedriver(download.url, target_path)

    downloaded_version = get_chromedriver_version(target_path)
    if not major_versions_match(downloaded_version, chrome_version):
        raise RuntimeError(
            f"Downloaded ChromeDriver still does not match Chrome. "
            f"Chrome={chrome_version}; ChromeDriver={downloaded_version}"
        )

    print(f"ChromeDriver 准备完成: {target_path}", flush=True)
    return str(target_path)


def fetch_driver_metadata(url: str = CHROME_FOR_TESTING_MILESTONES_URL) -> dict:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def choose_chromedriver_download(
    metadata: dict,
    chrome_major: int,
    platform_name: str,
) -> DriverDownload:
    milestone = metadata.get("milestones", {}).get(str(chrome_major))
    if not milestone:
        raise RuntimeError(f"Chrome for Testing has no ChromeDriver metadata for Chrome {chrome_major}")

    for item in milestone.get("downloads", {}).get("chromedriver", []):
        if item.get("platform") == platform_name and item.get("url"):
            return DriverDownload(version=milestone["version"], url=item["url"])

    raise RuntimeError(f"ChromeDriver for platform {platform_name} was not found for Chrome {chrome_major}")


def current_platform_name() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "windows":
        return "win64" if "64" in machine else "win32"
    if system == "darwin":
        return "mac-arm64" if machine in {"arm64", "aarch64"} else "mac-x64"
    if system == "linux":
        return "linux64"

    raise RuntimeError(f"Unsupported platform for ChromeDriver download: {system} {machine}")


def download_and_extract_chromedriver(url: str, target_path: str | Path) -> None:
    target = Path(target_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    zip_path = target.parent / "chromedriver-download.zip"
    extract_dir = target.parent / "_extract"

    if extract_dir.exists():
        shutil.rmtree(extract_dir)

    try:
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(extract_dir)

        extracted_driver = next(
            path
            for path in extract_dir.rglob(target.name)
            if path.is_file()
        )
        shutil.copy2(extracted_driver, target)
        target.chmod(0o755)
    finally:
        if zip_path.exists():
            zip_path.unlink()
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
