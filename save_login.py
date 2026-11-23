import os
import re
import sys

from dotenv import load_dotenv
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from utils.auth_state import (
    app_origin,
    capture_session_storage,
    save_session_storage,
    session_storage_path,
)

load_dotenv(override=True)

ROLES = {
    "super_admin": ("SUPERADMIN_USER_ID", "SUPERADMIN_PASSWORD"),
    "customer_administrator": ("Customer_Administrator_ID", "Customer_Administrator_PASSWORD"),
    "finance_coordinator": ("Finance_Coordinator_ID", "Finance_Coordinator_PASSWORD"),
}

role = sys.argv[1] if len(sys.argv) > 1 else "super_admin"
if role not in ROLES:
    raise SystemExit(f"Unknown role {role!r}. Choose from: {', '.join(ROLES)}")

base_url = os.getenv("BASE_URL")
user = os.getenv(ROLES[role][0])
pwd = os.getenv(ROLES[role][1])
if not base_url or not user or not pwd:
    raise RuntimeError(
        "BASE_URL and the selected role's username/password must be set in .env."
    )

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    try:
        page.goto(base_url)

        password_field = page.locator("input[type='password']").first
        password_field.wait_for(timeout=30000)
        username_field = page.locator(
            "input[type='email'], input[type='text'], input:not([type])"
        ).first
        username_field.fill(user)
        password_field.fill(pwd)

        print("Credentials filled. Solve the captcha and click Login in the browser.")
        try:
            page.wait_for_url(
                re.compile(r".*/dashboard/?(?:[?#].*)?$"),
                timeout=180000,
            )
        except PlaywrightTimeoutError as error:
            raise RuntimeError(
                "Login was not confirmed: the browser did not reach /dashboard "
                "within 3 minutes. Check the credentials, captcha, and any "
                "message shown on the login page. No state was saved."
            ) from error

        page.wait_for_load_state("domcontentloaded")
        os.makedirs(".auth", exist_ok=True)
        state_path = f".auth/{role}.json"
        context.storage_state(path=state_path)
        save_session_storage(
            session_storage_path(state_path),
            app_origin(base_url),
            capture_session_storage(page),
        )
        print(f"Login state saved for {role}.")
    finally:
        browser.close()
