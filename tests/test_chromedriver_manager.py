from pathlib import Path

from utils.chromedriver_manager import (
    DRIVER_DIR_NAME,
    choose_chromedriver_download,
    ensure_project_chromedriver,
    project_driver_path,
)


def test_project_driver_path_uses_project_drivers_directory(tmp_path):
    assert project_driver_path(tmp_path) == tmp_path / DRIVER_DIR_NAME / "chromedriver.exe"


def test_choose_chromedriver_download_prefers_matching_platform():
    metadata = {
        "milestones": {
            "149": {
                "version": "149.0.7827.103",
                "downloads": {
                    "chromedriver": [
                        {"platform": "linux64", "url": "https://example.test/linux.zip"},
                        {"platform": "win64", "url": "https://example.test/win.zip"},
                    ]
                },
            }
        }
    }

    download = choose_chromedriver_download(metadata, chrome_major=149, platform_name="win64")

    assert download.version == "149.0.7827.103"
    assert download.url == "https://example.test/win.zip"


def test_choose_chromedriver_download_fails_for_missing_major():
    try:
        choose_chromedriver_download({"milestones": {}}, chrome_major=149, platform_name="win64")
    except RuntimeError as exc:
        assert "Chrome 149" in str(exc)
    else:
        raise AssertionError("expected missing milestone to fail")


def test_choose_chromedriver_download_fails_for_missing_platform():
    metadata = {
        "milestones": {
            "149": {
                "version": "149.0.7827.103",
                "downloads": {"chromedriver": [{"platform": "linux64", "url": "https://example.test/linux.zip"}]},
            }
        }
    }

    try:
        choose_chromedriver_download(metadata, chrome_major=149, platform_name="win64")
    except RuntimeError as exc:
        assert "win64" in str(exc)
    else:
        raise AssertionError("expected missing platform to fail")


def test_ensure_project_chromedriver_force_refresh_downloads_even_when_existing_matches(tmp_path, monkeypatch):
    target = project_driver_path(tmp_path)
    target.parent.mkdir()
    target.write_text("old driver", encoding="utf-8")
    downloads = []

    monkeypatch.setattr("utils.chromedriver_manager.get_chrome_version", lambda: "Google Chrome 149.0.7827.103")
    monkeypatch.setattr(
        "utils.chromedriver_manager.get_chromedriver_version",
        lambda _path: "ChromeDriver 149.0.7827.103",
    )
    monkeypatch.setattr(
        "utils.chromedriver_manager.fetch_driver_metadata",
        lambda: {
            "milestones": {
                "149": {
                    "version": "149.0.7827.103",
                    "downloads": {
                        "chromedriver": [
                            {"platform": "win64", "url": "https://example.test/chromedriver.zip"}
                        ]
                    },
                }
            }
        },
    )
    monkeypatch.setattr("utils.chromedriver_manager.current_platform_name", lambda: "win64")

    def fake_download(url, path):
        downloads.append((url, Path(path)))

    monkeypatch.setattr("utils.chromedriver_manager.download_and_extract_chromedriver", fake_download)

    result = ensure_project_chromedriver(project_root=tmp_path, force_refresh=True)

    assert Path(result) == target
    assert downloads == [("https://example.test/chromedriver.zip", target)]
