import sys
from playwright.sync_api import sync_playwright
from utils.config import BASE_URL, USERS

role = sys.argv[1]
user_id, password = USERS[role]

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

    input(f"Solve the captcha, click Continue as {role}, wait for the dashboard, then press Enter...")

    context.storage_state(path=f".auth/{role}.json")
    browser.close()
    print(f"Saved .auth/{role}.json")
