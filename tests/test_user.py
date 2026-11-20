from datetime import date, timedelta
from uuid import uuid4

import pytest
from playwright.sync_api import expect

from pages.Management.user import UserManagementPage


ORGANIZATION = "SNV AVIATION PRIVATE LTD"
EDIT_ORGANIZATION = "BPCL"
EDIT_TARGET = "test admin user"
STATUS_TARGET = "SVN- Admin user"


@pytest.fixture
def users_page(super_admin_page):
    page = UserManagementPage(super_admin_page)
    page.open(ORGANIZATION)
    return page


def test_add_user(users_page):
    unique_id = uuid4().hex[:12]
    username = f"Management viewer {unique_id}"
    email = f"management-viewer-{unique_id}@example.com"
    mobile = f"9{uuid4().int % 1_000_000_000:09d}"
    start_date = (date.today() + timedelta(days=1)).isoformat()
    end_date = (date.today() + timedelta(days=30)).isoformat()

    users_page.open_add_user_form()
    users_page.fill_add_user_identity(
        username, email, mobile, start_date, end_date
    )
    expect(users_page.page.get_by_role("button", name="Invite User")).to_be_visible()
    users_page.select_new_user_role("Customer Administrator")
    users_page.select_new_user_role("Management Viewer")
    users_page.submit_add_user_form()

    expect(users_page.user_row(username)).to_be_visible()


def test_edit_user_name_and_restore_original(users_page):
    users_page.open(EDIT_ORGANIZATION)
    updated_username = f"{EDIT_TARGET} edited {uuid4().hex[:8]}"
    expect(users_page.user_row(EDIT_TARGET)).to_be_visible()

    try:
        users_page.edit_user(EDIT_TARGET, updated_username)
        expect(users_page.user_row(updated_username)).to_be_visible()
    finally:
        if users_page.user_row(updated_username).count():
            users_page.edit_user(updated_username, EDIT_TARGET)

    expect(users_page.user_row(EDIT_TARGET)).to_be_visible()


def test_deactivate_user_and_restore_original_status(users_page):
    was_active = users_page.user_is_active(STATUS_TARGET)

    try:
        users_page.set_user_active(STATUS_TARGET, active=True)
        users_page.deactivate_user(STATUS_TARGET)
        assert not users_page.user_is_active(STATUS_TARGET)
    finally:
        users_page.set_user_active(STATUS_TARGET, active=was_active)


def test_cancel_activation_keeps_user_inactive(users_page):
    was_active = users_page.user_is_active(STATUS_TARGET)

    try:
        users_page.set_user_active(STATUS_TARGET, active=False)
        users_page.activate_user(STATUS_TARGET, confirm=False)
        assert not users_page.user_is_active(STATUS_TARGET)
    finally:
        users_page.set_user_active(STATUS_TARGET, active=was_active)


def test_activate_user_and_restore_original_status(users_page):
    was_active = users_page.user_is_active(STATUS_TARGET)

    try:
        users_page.set_user_active(STATUS_TARGET, active=False)
        users_page.activate_user(STATUS_TARGET)
        assert users_page.user_is_active(STATUS_TARGET)
    finally:
        users_page.set_user_active(STATUS_TARGET, active=was_active)
