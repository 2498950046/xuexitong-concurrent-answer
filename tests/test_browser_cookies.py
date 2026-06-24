from utils.browser_cookies import apply_browser_cookies, capture_browser_cookies, cookie_domains


class CdpCookieDriver:
    def __init__(self):
        self.commands = []

    def execute_cdp_cmd(self, command, params):
        self.commands.append((command, params))
        if command == "Network.getAllCookies":
            return {
                "cookies": [
                    {
                        "name": "UID",
                        "value": "123",
                        "domain": ".chaoxing.com",
                        "path": "/",
                        "expires": -1,
                        "priority": "Medium",
                    }
                ]
            }
        return {}


def test_capture_browser_cookies_reads_all_cdp_cookies():
    driver = CdpCookieDriver()

    assert capture_browser_cookies(driver) == [
        {
            "name": "UID",
            "value": "123",
            "domain": ".chaoxing.com",
            "path": "/",
            "expires": -1,
            "priority": "Medium",
        }
    ]


def test_apply_browser_cookies_sanitizes_cdp_cookie_fields():
    driver = CdpCookieDriver()

    count = apply_browser_cookies(
        driver,
        [
            {
                "name": "UID",
                "value": "123",
                "domain": ".chaoxing.com",
                "path": "/",
                "expires": -1,
                "priority": "Medium",
            }
        ],
    )

    assert count == 1
    assert driver.commands[-1] == (
        "Network.setCookies",
        {"cookies": [{"name": "UID", "value": "123", "domain": ".chaoxing.com", "path": "/"}]},
    )


def test_cookie_domains_returns_unique_normalized_domains():
    assert cookie_domains(
        [
            {"domain": ".chaoxing.com"},
            {"domain": "chaoxing.com"},
            {"domain": ".mooc1.chaoxing.com"},
        ]
    ) == ["chaoxing.com", "mooc1.chaoxing.com"]
