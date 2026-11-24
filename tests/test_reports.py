import re
import zlib

import pytest

from pages.reports import ReportsPage

FDV_COLUMNS_TO_HIDE = [
    "Sr. No.",
    "Airfield",
    "Plant Code",
    "A/C Regi. No.",
    "Aircraft Type",
    "Next",
    "From",
]
DISPATCH_COLUMNS_TO_HIDE = ["Airfield", "Plant Code"]
def _pdf_content(download, tmp_path):
    pdf_path = tmp_path / download.suggested_filename
    download.save_as(pdf_path)
    pdf = pdf_path.read_bytes()
    streams = [pdf]
    for stream in re.findall(rb"stream\r?\n(.*?)\r?\nendstream", pdf, re.DOTALL):
        try:
            streams.append(zlib.decompress(stream))
        except zlib.error:
            continue
    return b"\n".join(streams)


def _rows_with_export_ids(page, checkbox_name):
    checkboxes = page.get_by_role(
        "checkbox", name=checkbox_name, exact=True
    )
    rows = []
    seen_identifiers = set()
    for index in range(checkboxes.count()):
        checkbox = checkboxes.nth(index)
        row = checkbox.locator("xpath=ancestor::*[@role='row'][1]")
        cells = row.locator(".MuiDataGrid-cell").all_inner_texts()
        identifier = next(
            (
                cell.strip()
                for cell in cells
                if re.fullmatch(r"[A-Z0-9]{10,}", cell.strip())
                and cell.strip() != "0000100599"
            ),
            None,
        )
        if identifier and identifier not in seen_identifiers:
            seen_identifiers.add(identifier)
            row_checkbox = (
                page.locator(".MuiDataGrid-row")
                .filter(has_text=identifier)
                .locator("input[name='select_row']")
                .first
            )
            rows.append((row_checkbox, identifier))
    return rows


def _clear_fdv_selection(page):
    select_all = page.get_by_role("checkbox", name="Select all rows")
    if not select_all.is_checked():
        select_all.check()
    select_all.uncheck()


@pytest.fixture
def reports(super_admin_page):
    return ReportsPage(super_admin_page)


def test_fdv_report_filters_columns_and_downloads_pdf(reports):
    reports.open_fdv_report()
    reports.select_customer_option("All customers")
    reports.select_customer_option("SNV AVIATION PRIVATE LTD")
    reports.select_customer_option("SNV AVIATION PRIVATE LTD")
    reports.select_customer_option("All customers")

    reports.set_date_range("2026-11-01", "2026-11-13")
    reports.open_columns()
    reports.hide_columns(FDV_COLUMNS_TO_HIDE)

    download = reports.download_pdf()
    assert download.failure() is None
    assert download.suggested_filename.lower().endswith(".pdf")


def test_fdv_report_downloads_selected_rows(reports, tmp_path):
    reports.open_fdv_report()
    page = reports.page
    _clear_fdv_selection(page)

    rows = _rows_with_export_ids(page, "Select row")
    assert len(rows) >= 3, "FDV report must have at least three selectable rows."
    selected_rows = rows[:3]
    for checkbox, _ in selected_rows:
        checkbox.check()

    assert page.get_by_role(
        "button", name="Download (3 selected)", exact=True
    ).is_visible()
    download = reports.download_pdf()
    assert download.failure() is None
    assert download.suggested_filename.lower().endswith(".pdf")
    pdf_content = _pdf_content(download, tmp_path)
    for _, identifier in selected_rows:
        assert identifier.encode() in pdf_content, (
            f"Selected FDV row {identifier!r} was missing from the exported PDF."
        )


def test_fdv_unchecked_rows_are_excluded_from_export(reports, tmp_path):
    reports.open_fdv_report()
    page = reports.page
    page.locator(".MuiDataGrid-row").first.wait_for(state="visible")
    select_all = page.get_by_role("checkbox", name="Select all rows")
    if not select_all.is_checked():
        select_all.check()

    selected_rows = _rows_with_export_ids(page, "Unselect row")
    assert len(selected_rows) > 3, (
        "FDV report must have rows remaining after unselecting three rows."
    )
    total_selected = len(selected_rows)
    unchecked_rows = selected_rows[:3]
    for checkbox, _ in unchecked_rows:
        checkbox.uncheck()

    assert total_selected > len(unchecked_rows)
    assert page.get_by_role(
        "button", name=re.compile(r"^Download \(\d+ selected\)$")
    ).is_visible()
    download = reports.download_pdf()
    assert download.failure() is None
    pdf_content = _pdf_content(download, tmp_path)
    for _, identifier in unchecked_rows:
        assert identifier.encode() not in pdf_content, (
            f"Unchecked FDV row {identifier!r} was included in the exported PDF."
        )


def test_dispatch_report_filters_columns_and_downloads_selected_rows(reports):
    reports.open_dispatch_report()
    page = reports.page
    reports.select_customer_option("All customers")
    reports.set_date_range("2026-11-01", "2026-11-13")

    reports.open_filters()
    page.get_by_role("textbox", name="Plant").click()
    page.get_by_role("option", name="- Delhi (T-1)").click()
    page.get_by_role("textbox", name="Plant").click()
    page.get_by_role("button", name="All plants").click()
    reports.close_filters()

    reports.open_columns()
    reports.hide_columns(DISPATCH_COLUMNS_TO_HIDE)

    rows = page.locator(".MuiDataGrid-row")
    for row_index in range(3):
        rows.nth(row_index).locator("input[name='select_row']").check()

    assert page.get_by_role(
        "button", name="Download (3 selected)", exact=True
    ).is_visible()
    download = reports.download_pdf()
    assert download.failure() is None
    assert download.suggested_filename.lower().endswith(".pdf")


def test_dispatch_unchecked_rows_are_excluded_from_export(reports, tmp_path):
    reports.open_dispatch_report()
    page = reports.page
    reports.select_customer_option("All customers")
    select_all = page.get_by_role("checkbox", name="Select all rows")
    if not select_all.is_checked():
        select_all.check()
    selected_rows = _rows_with_export_ids(page, "Unselect row")
    assert len(selected_rows) > 3, (
        "Dispatch report must have rows remaining after unselecting three rows."
    )
    total_selected = len(selected_rows)
    unchecked_rows = selected_rows[:3]
    for checkbox, _ in unchecked_rows:
        checkbox.uncheck()

    assert total_selected > len(unchecked_rows)
    assert page.get_by_role(
        "button", name=re.compile(r"^Download \(\d+ selected\)$")
    ).is_visible()
    download = reports.download_pdf()
    assert download.failure() is None
    pdf_content = _pdf_content(download, tmp_path)
    for _, identifier in unchecked_rows:
        assert identifier.encode() not in pdf_content, (
            "Unchecked dispatch row was included in the exported PDF: "
            f"{identifier!r}."
        )


def test_soa_report_opens_with_default_dates(reports):
    reports.open_soa_report()
    from_date = reports.page.get_by_role("textbox", name="From date").input_value()
    to_date = reports.page.get_by_role("textbox", name="To date").input_value()
    assert from_date == "", (
        f"SOA From date was selected automatically: {from_date!r}."
    )
    assert to_date == "", (
        f"SOA To date was selected automatically: {to_date!r}."
    )
