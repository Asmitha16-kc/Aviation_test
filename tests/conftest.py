import os
from urllib.parse import urlsplit

import pytest

from utils.auth_state import (
    app_origin,
    capture_session_storage,
    restore_session_storage,
    save_session_storage,
    session_storage_path,
)
from utils.config import BASE_URL

os.makedirs(".auth", exist_ok=True)

TIMEOUT = 10000


def _save_state(context, role, page):
    state_path = f".auth/{role}.json"
    context.storage_state(path=state_path)
    save_session_storage(
        session_storage_path(state_path),
        app_origin(BASE_URL),
        capture_session_storage(page),
    )


def _start(browser, role):
    path = f".auth/{role}.json"
    if not os.path.exists(path):
        pytest.skip(f"{path} missing. Run: python save_login.py {role}")
    context = browser.new_context(storage_state=path)
    restore_session_storage(
        context, session_storage_path(path), app_origin(BASE_URL)
    )
    context.set_default_timeout(TIMEOUT)
    page = context.new_page()
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_load_state("networkidle")
    dashboard_path = urlsplit(f"{BASE_URL}/dashboard").path.rstrip("/")
    current_path = urlsplit(page.url).path.rstrip("/")
    if current_path != dashboard_path:
        context.close()
        pytest.fail(
            f"Saved login state for {role!r} was rejected. "
            f"Run: python save_login.py {role}"
        )
    _save_state(context, role, page)
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
    _save_state(context, "super_admin", page)
    context.close()


@pytest.fixture(scope="session")
def _customer_admin_session(browser):
    context, page = _start(browser, "customer_administrator")
    yield page
    _save_state(context, "customer_administrator", page)
    context.close()


@pytest.fixture(scope="session")
def _finance_session(browser):
    context, page = _start(browser, "finance_coordinator")
    yield page
    _save_state(context, "finance_coordinator", page)
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