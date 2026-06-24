from __future__ import annotations

from selenium.common.exceptions import WebDriverException


COOKIE_PARAM_KEYS = {
    "name",
    "value",
    "domain",
    "path",
    "secure",
    "httpOnly",
    "sameSite",
    "expires",
}


def capture_browser_cookies(driver) -> list[dict]:
    try:
        result = driver.execute_cdp_cmd("Network.getAllCookies", {})
        cookies = result.get("cookies", [])
        if cookies:
            return [dict(cookie) for cookie in cookies]
    except (AttributeError, WebDriverException):
        pass

    try:
        return [dict(cookie) for cookie in driver.get_cookies()]
    except WebDriverException:
        return []


def apply_browser_cookies(driver, cookies: list[dict]) -> int:
    sanitized = [_sanitize_cookie(cookie) for cookie in cookies]
    sanitized = [cookie for cookie in sanitized if cookie.get("name") and cookie.get("value") is not None]
    if not sanitized:
        return 0

    try:
        driver.execute_cdp_cmd("Network.setCookies", {"cookies": sanitized})
        return len(sanitized)
    except (AttributeError, WebDriverException):
        pass

    return _apply_cookies_with_webdriver(driver, sanitized)


def _sanitize_cookie(cookie: dict) -> dict:
    sanitized = {key: value for key, value in cookie.items() if key in COOKIE_PARAM_KEYS}
    if "expiry" in cookie and "expires" not in sanitized:
        sanitized["expires"] = cookie["expiry"]

    expires = sanitized.get("expires")
    if expires is None or expires <= 0:
        sanitized.pop("expires", None)
    return sanitized


def _apply_cookies_with_webdriver(driver, cookies: list[dict]) -> int:
    applied = 0
    for cookie in cookies:
        domain = str(cookie.get("domain") or "").lstrip(".")
        if not domain:
            continue
        try:
            driver.get(f"https://{domain}/")
            driver.add_cookie(_to_webdriver_cookie(cookie))
            applied += 1
        except WebDriverException:
            continue
    return applied


def _to_webdriver_cookie(cookie: dict) -> dict:
    result = {
        "name": cookie["name"],
        "value": cookie["value"],
        "path": cookie.get("path", "/"),
    }
    if cookie.get("domain"):
        result["domain"] = cookie["domain"]
    if cookie.get("secure") is not None:
        result["secure"] = bool(cookie["secure"])
    if cookie.get("httpOnly") is not None:
        result["httpOnly"] = bool(cookie["httpOnly"])
    if cookie.get("sameSite") in {"Strict", "Lax", "None"}:
        result["sameSite"] = cookie["sameSite"]
    if cookie.get("expires"):
        result["expiry"] = int(cookie["expires"])
    return result


def cookie_domains(cookies: list[dict]) -> list[str]:
    domains = []
    seen = set()
    for cookie in cookies:
        domain = str(cookie.get("domain") or "").lstrip(".")
        if not domain or domain in seen:
            continue
        seen.add(domain)
        domains.append(domain)
    return domains
