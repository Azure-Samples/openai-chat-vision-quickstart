"""Minimal end-to-end browser test using Playwright.

Usage:
    python scripts/e2e_chat_playwright.py https://your-app.azurecontainerapps.io

Only one argument is accepted: the base URL of the deployed app.
No environment variables or azd lookups are performed.
"""

from __future__ import annotations

import re
import sys
import time

from playwright.sync_api import Playwright, expect, sync_playwright


def run_test(pw: Playwright, base_url: str) -> None:
    # Internal test configuration (adjust here if needed)
    message = "Hi"
    timeout = 60  # seconds
    headless = True
    expected_substring = None  # Set to a string to force exact substring match
    greeting_regex = r"\b(H(i|ello))\b"
    browser = pw.chromium.launch(headless=headless)
    context = browser.new_context()
    page = context.new_page()

    if not base_url.startswith("http"):
        raise ValueError("Base URL must start with http/https")
    base_url = base_url.rstrip("/")

    url = base_url
    if not url.endswith("/"):
        url += "/"
    print(f"Navigating to {url}")
    page.goto(url, wait_until="domcontentloaded")

    textbox = page.get_by_role("textbox", name="Ask ChatGPT")
    textbox.click()
    textbox.fill(message)
    textbox.press("Enter")
    # Redundant click in case Enter doesn't submit on some platforms
    page.get_by_role("button", name="Send").click()

    # Wait for the last assistant message content div that is not the typing indicator
    content_locator = page.locator(".toast-body.message-content").last
    # Poll until the content no longer contains 'Typing...' and has some text
    start = time.time()
    while time.time() - start < timeout:
        txt = content_locator.inner_text().strip()
        if txt and "Typing..." not in txt:
            break
        time.sleep(0.5)
    else:
        raise RuntimeError("Timeout waiting for assistant response")

    txt_final = content_locator.inner_text().strip()
    if expected_substring:
        expect(content_locator).to_contain_text(expected_substring)
    else:
        if not re.search(greeting_regex, txt_final, flags=re.IGNORECASE):
            raise RuntimeError(
                f"Assistant response did not match greeting regex '{greeting_regex}'. Got: {txt_final[:120]}"
            )
        if len(txt_final) < 2:
            raise RuntimeError("Assistant response too short")
    print("Assistant response snippet:", txt_final[:160])

    # Cleanup
    context.close()
    browser.close()


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/e2e_chat_playwright.py <base_url>", file=sys.stderr)
        return 1
    base_url = sys.argv[1]
    try:
        with sync_playwright() as pw:
            run_test(pw, base_url)
        print("Playwright E2E test succeeded.")
        return 0
    except Exception as e:  # broad for CLI convenience
        print(f"Playwright E2E test failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
