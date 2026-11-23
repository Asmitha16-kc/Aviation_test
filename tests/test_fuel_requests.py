import pytest
from playwright.sync_api import expect

from pages.modules.fuel_requests import STATUS_TABS, FuelRequestsPage


@pytest.fixture
def fuel_requests(customer_admin_page):
    requests_page = FuelRequestsPage(customer_admin_page)
    requests_page.open()
    return requests_page


def test_tc01_reject_other_org_flight_with_same_route_city(fuel_requests):
    fuel_requests.open_new_request()
    city = "ATQ – Amritsar, Punjab, India"
    fuel_requests.fill_required_fields(
        flight_no="QQ1879",
        from_city=city,
        next_city=city,
        destination_city=city,
    )
    try:
        submitted = fuel_requests.attempt_submit_request()
    finally:
        fuel_requests.close_new_request()
    assert not submitted, (
        "TC01 failed: Flight QQ1879 (World Fuel Services) was accepted with "
        "the same city in From, Next, and Destination."
    )


def test_tc02_save_draft_with_only_some_fields(fuel_requests):
    fuel_requests.open_new_request()
    fuel_requests.select_station("AGL – JSPL Angul")
    fuel_requests.select_aircraft("VTYAB – B737")
    fuel_requests.page.get_by_role(
        "textbox", name="Flight No. *"
    ).fill("0A 1234")

    failed_toast = fuel_requests.page.get_by_text(
        "Failed to submit fuel request", exact=True
    )
    try:
        fuel_requests.save_draft_button.click()
        expect(failed_toast).to_be_hidden(timeout=3000)
        expect(fuel_requests.save_draft_button).to_be_hidden(timeout=10000)
    finally:
        fuel_requests.close_new_request()


def test_tc03_flight_number_field_shows_format_example(fuel_requests):
    fuel_requests.open_new_request()
    flight_number = fuel_requests.page.get_by_role(
        "textbox", name="Flight No. *"
    )
    try:
        assert flight_number.get_attribute("placeholder") == "e.g. AI 101", (
            "TC03 failed: The flight-number field does not show the example "
            "'e.g. AI 101'."
        )
    finally:
        fuel_requests.close_new_request()


def test_tc04_reject_flight_number_with_invalid_format(fuel_requests):
    fuel_requests.open_new_request()
    fuel_requests.fill_required_fields(flight_no="AK7077S")
    try:
        submitted = fuel_requests.attempt_submit_request()
    finally:
        fuel_requests.close_new_request()

    assert not submitted, (
        "TC04 failed: Flight number AK7077S was accepted; expected an "
        "airline code and number such as AI 101."
    )


def test_tc05_each_status_tab_can_be_selected(fuel_requests):
    for status in STATUS_TABS:
        tab = fuel_requests.status_tab(status)
        tab.click()
        expect(tab).to_have_attribute("aria-selected", "true")
