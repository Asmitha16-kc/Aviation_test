import sys
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright
from utils.auth_state import (
    app_origin,
    capture_session_storage,
    restore_session_storage,
    save_session_storage,
    session_storage_path,
)
from utils.config import BASE_URL, USERS

role = sys.argv[1]
user_id, password = USERS[role]
state_path = Path(".auth") / f"{role}.json"
if not BASE_URL:
    raise RuntimeError("BASE_URL must be configured before saving a login state.")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(BASE_URL)

    try:
        page.get_by_role("textbox", name="User ID").fill(user_id or "")
        page.get_by_role("textbox", name="Password").fill(password or "")
    except Exception:
        print("Could not auto-fill. Type the ID and password manually.")

    try:
        input(
            f"Solve the captcha, click Continue as {role}, and press Enter "
            "after the dashboard appears..."
        )
        page.wait_for_url("**/dashboard**", timeout=60000)
        page.wait_for_load_state("networkidle")

        state_path.parent.mkdir(parents=True, exist_ok=True)
        session_path = session_storage_path(state_path)
        origin = app_origin(BASE_URL)
        save_session_storage(
            session_path, origin, capture_session_storage(page)
        )
        context.storage_state(path=str(state_path))

        validation_context = browser.new_context(storage_state=str(state_path))
        try:
            restore_session_storage(validation_context, session_path, origin)
            validation_page = validation_context.new_page()
            validation_page.goto(f"{BASE_URL}/dashboard")
            validation_page.wait_for_load_state("networkidle")
            dashboard_path = urlsplit(validation_page.url).path.rstrip("/")
            if dashboard_path != "/dashboard":
                raise RuntimeError(
                    "The saved login state was rejected. Complete the login "
                    "again and wait for the dashboard before saving."
                )
            save_session_storage(
                session_path, origin, capture_session_storage(validation_page)
            )
            validation_context.storage_state(path=str(state_path))
        finally:
            validation_context.close()
    finally:
        browser.close()

print(f"Saved and verified {state_path}")
