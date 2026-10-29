from playwright.sync_api import expect
from utils.config import BASE_URL


def test_verify_super_admin_lands_on_dashboard(super_admin_page):
    super_admin_page.goto(f"{BASE_URL}/dashboard")
    expect(super_admin_page).to_have_url(f"{BASE_URL}/dashboard")
