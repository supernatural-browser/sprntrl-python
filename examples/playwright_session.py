"""End-to-end: create session, connect via Playwright, screenshot, stop.

Requires: pip install 'sprntrl[playwright]' && playwright install chromium
"""

from sprntrl import Sprntrl


def main() -> None:
    with Sprntrl() as client:
        session = client.sessions.create(os="macos", location="us-east")
        try:
            browser = client.sessions.connect(
                session["id"], auto_whitelist=True
            )
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()

            page.goto("https://bot.sannysoft.com", wait_until="domcontentloaded")
            page.screenshot(path="sannysoft.png", full_page=True)
            print(f"saved sannysoft.png (session {session['id']})")

            browser.close()
        finally:
            client.sessions.stop(session["id"])


if __name__ == "__main__":
    main()
