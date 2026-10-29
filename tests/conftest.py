import os
import pytest
from utils.config import BASE_URL

os.makedirs(".auth", exist_ok=True)

TIMEOUT = 10000


def _start(browser, role):
    path = f".auth/{role}.json"
    if not os.path.exists(path):
        pytest.skip(f"{path} missing. Run: python save_login.py {role}")
    context = browser.new_context(storage_state=path)
    context.set_default_timeout(TIMEOUT)
    page = context.new_page()
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_load_state("networkidle")
    if "session-expired" in page.url or "/login" in page.url:
        context.close()
        pytest.skip(f"Session expired. Run: python save_login.py {role}")
    return context, page


def _reset(page):
    # close any popup or dropdown the previous test left open
    page.keyboard.press("Escape")
    page.keyboard.press("Escape")


# ---------- one window per role, shared by all tests ----------
@pytest.fixture(scope="session")
def _super_admin_session(browser):
    context, page = _start(browser, "super_admin")
    yield page
    context.close()


@pytest.fixture(scope="session")
def _customer_admin_session(browser):
    context, page = _start(browser, "customer_administrator")
    yield page
    context.close()


@pytest.fixture(scope="session")
def _finance_session(browser):
    context, page = _start(browser, "finance_coordinator")
    yield page
    context.close()


# ---------- fixtures used by the tests ----------
@pytest.fixture
def super_admin_page(_super_admin_session):
    _reset(_super_admin_session)
    return _super_admin_session


@pytest.fixture
def customer_admin_page(_customer_admin_session):
    _reset(_customer_admin_session)
    return _customer_admin_session


@pytest.fixture
def finance_page(_finance_session):
    _reset(_finance_session)
    return _finance_session