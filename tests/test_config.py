from utils.config import AppConfig


def test_app_config_reads_environment(monkeypatch):
    monkeypatch.setenv("XUEXITONG_PHONE", "13800000000")
    monkeypatch.setenv("XUEXITONG_PASSWORD", "secret")
    monkeypatch.setenv("XUEXITONG_CHROMEDRIVER", "D:/tools/chromedriver.exe")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-reasoner")
    monkeypatch.setenv("XUEXITONG_BATCH_SIZE", "10")
    monkeypatch.setenv("XUEXITONG_WORK_URL", "https://example.com/work")

    config = AppConfig.from_env()

    assert config.phone == "13800000000"
    assert config.password == "secret"
    assert config.chromedriver_path == "D:/tools/chromedriver.exe"
    assert config.deepseek_api_key == "sk-test"
    assert config.deepseek_model == "deepseek-reasoner"
    assert config.batch_size == 10
    assert config.work_url == "https://example.com/work"


def test_app_config_uses_safe_defaults(monkeypatch):
    for key in [
        "XUEXITONG_PHONE",
        "XUEXITONG_PASSWORD",
        "XUEXITONG_CHROMEDRIVER",
        "DEEPSEEK_API_KEY",
        "DEEPSEEK_MODEL",
        "XUEXITONG_BATCH_SIZE",
        "XUEXITONG_WORK_URL",
    ]:
        monkeypatch.delenv(key, raising=False)

    config = AppConfig.from_env()

    assert config.login_url == "https://passport2.chaoxing.com/login"
    assert config.deepseek_base_url == "https://api.deepseek.com"
    assert config.deepseek_model == "deepseek-v4-pro"
    assert config.batch_size == 20


def test_app_config_reads_dotenv_file(monkeypatch, tmp_path):
    for key in [
        "XUEXITONG_PHONE",
        "XUEXITONG_PASSWORD",
        "DEEPSEEK_API_KEY",
        "DEEPSEEK_MODEL",
    ]:
        monkeypatch.delenv(key, raising=False)

    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "\n".join(
            [
                "XUEXITONG_PHONE=13800000000",
                "XUEXITONG_PASSWORD=secret",
                "DEEPSEEK_API_KEY=sk-test",
                "DEEPSEEK_MODEL=deepseek-v4-pro",
            ]
        ),
        encoding="utf-8",
    )

    config = AppConfig.from_env(env={}, dotenv_path=dotenv_path)

    assert config.phone == "13800000000"
    assert config.password == "secret"
    assert config.deepseek_api_key == "sk-test"
    assert config.deepseek_model == "deepseek-v4-pro"


def test_environment_overrides_dotenv(monkeypatch, tmp_path):
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("DEEPSEEK_MODEL=deepseek-v4-pro", encoding="utf-8")

    config = AppConfig.from_env(dotenv_path=dotenv_path)

    assert config.deepseek_model == "deepseek-v4-flash"


def test_require_existing_chromedriver_rejects_missing_path(monkeypatch, tmp_path):
    missing_path = tmp_path / "missing" / "chromedriver.exe"
    config = AppConfig(chromedriver_path=str(missing_path))

    try:
        config.require_existing_chromedriver()
    except FileNotFoundError as exc:
        assert "XUEXITONG_CHROMEDRIVER" in str(exc)
    else:
        raise AssertionError("expected missing chromedriver path to fail")


def test_app_config_reads_worker_count(monkeypatch):
    monkeypatch.setenv("XUEXITONG_WORKER_COUNT", "4")

    config = AppConfig.from_env()

    assert config.worker_count == 4


def test_app_config_worker_count_default(monkeypatch):
    monkeypatch.delenv("XUEXITONG_WORKER_COUNT", raising=False)

    config = AppConfig.from_env(env={})

    assert config.worker_count == 4


def test_app_config_rejects_invalid_worker_count(monkeypatch):
    monkeypatch.setenv("XUEXITONG_WORKER_COUNT", "0")

    try:
        AppConfig.from_env()
    except ValueError as exc:
        assert "XUEXITONG_WORKER_COUNT" in str(exc)
    else:
        raise AssertionError("expected invalid worker count to fail")
