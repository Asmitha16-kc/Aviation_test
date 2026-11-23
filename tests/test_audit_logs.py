from datetime import datetime
import re
import pytest
from playwright.sync_api import expect
from pages.audit_logs import AuditLogsPage

SEARCH_TEXT = "regional head"
ACTION = "Login success"
ACTION_OPTIONS_TO_CHECK = [ACTION, "Logout"]
ORGANIZATION = "BPCL"
ENTITY = "USER"
DATE_RANGE = ("2026-10-21", "2026-10-28")
COLUMNS_TO_HIDE = ["Organization", "Actor", "Entity"]
USER_EXPORT_ACTION = re.compile(
    r"(?:user.*(?:export|download)|(?:export|download).*user|excel)", re.I
)


@pytest.fixture
def audit_logs(super_admin_page):
    audit = AuditLogsPage(super_admin_page)
    audit.open()
    return audit


def wait_for_rows(audit):
    """Wait for the table to load. Skip the test if there are no records."""
    audit.page.wait_for_load_state("networkidle")
    try:
        expect(audit.rows.first).to_be_visible(timeout=8000)
    except AssertionError:
        pytest.skip("No records to check")


def expect_rows_contain(audit, *values):
    audit.page.wait_for_load_state("networkidle")
    for value in values:
        expect(
            audit.rows.filter(has_text=re.compile(re.escape(value), re.I)).first
        ).to_be_visible()
    rows = audit.rows.all_inner_texts()
    assert rows, "Expected matching audit-log rows"
    for row in rows:
        for value in values:
            assert re.search(re.escape(value), row, re.I), (
                f"Expected row to contain {value!r}, got {row!r}"
            )


def test_audit_logs_page_and_actor_search(audit_logs):
    audit = audit_logs
    expect(audit.heading).to_be_visible()
    audit.search_by_actor(SEARCH_TEXT)
    try:
        expect_rows_contain(audit, SEARCH_TEXT)
    finally:
        if audit.search_box.input_value():
            audit.clear_search()
    expect(audit.search_box).to_have_value("")


def test_audit_log_details_open_and_close(audit_logs):
    audit = audit_logs
    wait_for_rows(audit)
    audit.open_first_log()
    expect(audit.popup).to_be_visible()
    audit.close_popup()
    expect(audit.popup).not_to_be_visible()


def test_hide_three_columns_in_one_session(audit_logs):
    audit = audit_logs
    wait_for_rows(audit)
    audit.open_columns()
    try:
        for column in COLUMNS_TO_HIDE:
            audit.hide_column(column)
            expect(audit.column_header(column)).not_to_be_visible()
        audit.show_all_columns()
    finally:
        audit.page.keyboard.press("Escape")
    for column in COLUMNS_TO_HIDE:
        expect(audit.column_header(column)).to_be_visible()


def test_filter_panel_applies_organization_entity_and_date_range(audit_logs):
    audit = audit_logs
    audit.action_filter.click()
    for action in ACTION_OPTIONS_TO_CHECK:
        expect(
            audit.page.get_by_role("option", name=action, exact=True)
        ).to_be_visible()
    audit.page.get_by_role("option", name=ACTION, exact=True).click()
    audit.open_filters()
    audit.select_organization(ORGANIZATION)
    audit.select_entity(ENTITY)
    audit.set_date_range(*DATE_RANGE)
    audit.close_filters_btn.click()

    expect(audit.action_filter).to_contain_text(ACTION)
    expect(
        audit.page.get_by_role("button", name=f"Action: {ACTION}", exact=True)
    ).to_be_visible()
    expect(
        audit.page.get_by_role(
            "button", name=f"Organization: {ORGANIZATION}", exact=True
        )
    ).to_be_visible()
    expect(
        audit.page.get_by_role("button", name=f"Entity: {ENTITY}", exact=True)
    ).to_be_visible()
    expect(
        audit.page.get_by_role("button", name="From: 21/10/2026", exact=True)
    ).to_be_visible()
    expect(
        audit.page.get_by_role("button", name="To: 28/10/2026", exact=True)
    ).to_be_visible()

    expect_rows_contain(audit, ACTION, ORGANIZATION, ENTITY)
    start = datetime.fromisoformat(DATE_RANGE[0]).date()
    end = datetime.fromisoformat(DATE_RANGE[1]).date()
    for row in audit.rows.all():
        timestamp = row.get_by_role("gridcell").first.inner_text()
        row_date = datetime.strptime(timestamp, "%d/%m/%Y %H:%M").date()
        assert start <= row_date <= end


def test_user_directory_excel_export_is_recorded_in_audit_logs(audit_logs):
    page = audit_logs.page

    clear_all_chip = page.get_by_role("button", name="Clear all", exact=True)
    if clear_all_chip.count():
        clear_all_chip.click()

    page.get_by_role("button", name="Users").click()
    page.get_by_role("button", name="User directory").click()
    expect(page.get_by_role("heading", name="User Management")).to_be_visible()

    page.get_by_role("combobox", name="Organization").click()
    page.get_by_role("option", name=ORGANIZATION, exact=True).click()
    download_button = page.get_by_role("button", name="Download", exact=True)
    expect(download_button).to_be_enabled()
    download_button.click()

    with page.expect_download() as download_info:
        page.get_by_role("menuitem", name="Download as Excel").click()
    download = download_info.value
    assert download.failure() is None
    assert download.suggested_filename.lower().endswith(".xlsx")

    page.get_by_role("button", name="Audit Logs").click()
    expect(audit_logs.heading).to_be_visible()
    page.wait_for_load_state("networkidle")

    refresh_button = page.get_by_role("button", name="Refresh")
    if refresh_button.is_enabled():
        refresh_button.click()

    expect(audit_logs.rows.first).to_be_visible()
    audit_rows = audit_logs.rows.all_inner_texts()
    matching_export_rows = [
        row
        for row in audit_rows
        if USER_EXPORT_ACTION.search(row) and re.search(r"\bUSER\b", row, re.I)
    ]
    assert matching_export_rows, (
        f"Downloaded {download.suggested_filename}, but no matching USER export "
        "event appeared on the current Audit Logs page."
    )
