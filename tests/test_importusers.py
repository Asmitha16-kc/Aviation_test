import pytest
from playwright.sync_api import expect

from pages.import_users import ImportUsersPage


@pytest.fixture
def import_users_page(super_admin_page):
    import_page = ImportUsersPage(super_admin_page)
    import_page.open()
    yield import_page

    back_button = import_page.page.get_by_role("button", name="Back to users")
    if back_button.count() and back_button.is_visible():
        back_button.click()


def expect_upload_rejected(page):
    expect(page.get_by_role("alert")).to_be_visible()


def expect_csv_ready_for_defaults(page):
    expect(
        page.get_by_role("button", name="Apply Defaults & Preview")
    ).to_be_visible()


def test_users_header_only_csv_is_rejected(import_users_page):
    import_users_page.upload_csv("users_header_only.csv")
    expect_upload_rejected(import_users_page.page)


def test_empty_users_csv_is_rejected(import_users_page):
    import_users_page.upload_csv("users_empty.csv")
    expect_upload_rejected(import_users_page.page)


def test_special_users_csv_is_accepted_for_preview(import_users_page):
    import_users_page.upload_csv("users_special.csv")
    expect_csv_ready_for_defaults(import_users_page.page)


def test_users_wrong_header_csv_is_rejected(import_users_page):
    import_users_page.upload_csv("users_wrong_header.csv")
    expect_upload_rejected(import_users_page.page)


def test_invalid_users_csv_shows_network_error(import_users_page):
    import_users_page.upload_csv("users_invalid.csv")
    expect(import_users_page.page.get_by_role("alert")).to_have_text("Network Error")


def test_valid_users_csv_is_accepted_for_preview(import_users_page):
    import_users_page.upload_csv("users_valid.csv")
    expect_csv_ready_for_defaults(import_users_page.page)
