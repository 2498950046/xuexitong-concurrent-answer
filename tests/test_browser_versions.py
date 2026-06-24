from utils.browser_versions import (
    ensure_matching_major_versions,
    get_chrome_version,
    get_chrome_version_from_install_dir,
    major_versions_match,
    parse_major_version,
)


def test_parse_major_version_extracts_first_number():
    assert parse_major_version("ChromeDriver 143.0.7499.40") == 143
    assert parse_major_version("Google Chrome 149.0.7827.103") == 149


def test_parse_major_version_returns_none_for_unknown_text():
    assert parse_major_version("not a version") is None


def test_ensure_matching_major_versions_allows_missing_values():
    ensure_matching_major_versions(None, "Google Chrome 149.0.7827.103")
    ensure_matching_major_versions("ChromeDriver 149.0.7827.103", None)


def test_ensure_matching_major_versions_rejects_mismatch():
    try:
        ensure_matching_major_versions(
            "ChromeDriver 143.0.7499.40",
            "Google Chrome 149.0.7827.103",
        )
    except RuntimeError as exc:
        message = str(exc)
        assert "ChromeDriver 143" in message
        assert "Chrome 149" in message
    else:
        raise AssertionError("expected mismatched major versions to fail")


def test_major_versions_match_compares_only_major_number():
    assert major_versions_match("ChromeDriver 149.0.1", "Google Chrome 149.2.3")
    assert not major_versions_match("ChromeDriver 143.0.1", "Google Chrome 149.2.3")


def test_get_chrome_version_from_install_dir_reads_version_directory(tmp_path):
    chrome = tmp_path / "Application" / "chrome.exe"
    chrome.parent.mkdir()
    chrome.write_text("", encoding="utf-8")
    (chrome.parent / "149.0.7827.103").mkdir()
    (chrome.parent / "SetupMetrics").mkdir()

    assert get_chrome_version_from_install_dir(chrome) == "149.0.7827.103"


def test_get_chrome_version_falls_back_when_command_output_is_not_a_version(tmp_path, monkeypatch):
    chrome = tmp_path / "Application" / "chrome.exe"
    chrome.parent.mkdir()
    chrome.write_text("", encoding="utf-8")
    (chrome.parent / "149.0.7827.103").mkdir()

    monkeypatch.setattr(
        "utils.browser_versions.get_command_version",
        lambda _command: "正在现有的浏览器会话中打开。",
    )

    assert get_chrome_version(chrome) == "149.0.7827.103"
