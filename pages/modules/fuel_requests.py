import re
from datetime import datetime, timedelta

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect

from pages.base_page import BasePage
from utils.config import BASE_URL


STATUS_TABS = (
    "Draft",
    "Pending review",
    "Accepted",
    "Declined",
    "Modification required",
    "Expired",
    "Cancelled",
    "All",
)


class FuelRequestsPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.fuel_requests_button = page.get_by_role(
            "button", name="Fuel Requests"
        )
        self.new_request_button = page.get_by_role(
            "button", name="New Fuel Request"
        )
        self.save_draft_button = page.get_by_role(
            "button", name="Save as Draft"
        )
        self.submit_button = page.get_by_role(
            "button", name="Submit Fuel Request"
        )
        self.confirm_submit_button = page.get_by_role(
            "button", name="Confirm & Proceed"
        )
        self.submit_anyway_button = page.get_by_role(
            "button", name="Submit anyway", exact=True
        )

    def open(self):
        if self.new_request_button.is_visible():
            return
        if not self.fuel_requests_button.is_visible():
            self.page.goto(f"{BASE_URL}/dashboard")
        self.fuel_requests_button.click()
        expect(self.new_request_button).to_be_visible()

    def open_new_request(self):
        self.new_request_button.click()
        expect(self.save_draft_button).to_be_visible()

    def status_tab(self, name):
        return self.page.get_by_role("tab", name=name, exact=True)

    def select_station(self, name):
        self.page.get_by_role("combobox", name="Select a plant").click()
        self.page.get_by_role("option", name=name, exact=True).click()

    def select_aircraft(self, name):
        aircraft = self.page.get_by_role(
            "combobox", name=re.compile(r"^Aircraft Reg\. No\.")
        )
        aircraft.click()
        self.page.get_by_role("option", name=name, exact=True).click()

    def select_city(self, field_name, city):
        city_field = self.page.get_by_role(
            "combobox", name=re.compile(rf"^{re.escape(field_name)}")
        )
        city_field.click()
        self.page.get_by_role("option", name=city).click()

    def fill_required_fields(
        self,
        flight_no="0A 1234",
        from_city="AZH – Azamgarh, Uttar Pradesh",
        next_city="AYJ – Ayodhya, Uttar Pradesh",
        destination_city="AKD – Akola, Maharashtra",
    ):
        self.select_station("AGL – JSPL Angul")
        self.select_aircraft("VTYAB – B737")

        self.page.get_by_role("textbox", name="Flight No. *").fill(flight_no)
        fueling_time = (datetime.now() + timedelta(days=1)).replace(
            hour=5, minute=0, second=0, microsecond=0
        )
        self.page.get_by_role("textbox", name="Scheduled Fueling Time *").fill(
            fueling_time.strftime("%Y-%m-%dT%H:%M")
        )
        self.page.get_by_role("textbox", name="Expected Arrival Time *").fill(
            "04:30"
        )
        self.page.get_by_role("textbox", name="Expected Departure Time *").fill(
            "06:00"
        )

        self.select_city("From City", from_city)
        self.select_city("Next City", next_city)
        self.select_city("Destination City", destination_city)
        self.page.get_by_role("spinbutton", name="Expected Volume *").fill("100")

    def attempt_submit_request(self):
        self.submit_button.click()
        for _ in range(3):
            if self.submit_anyway_button.is_visible():
                self.submit_anyway_button.click()
            elif self.confirm_submit_button.is_visible():
                self.confirm_submit_button.click()
            else:
                break

        try:
            self.submit_button.wait_for(state="hidden", timeout=10000)
        except PlaywrightTimeoutError:
            return False
        return True

    def close_new_request(self):
        if not self.save_draft_button.is_visible():
            return
        close_button = self.page.get_by_label("Close")
        if close_button.count():
            close_button.last.click()
        else:
            self.page.keyboard.press("Escape")
        expect(self.save_draft_button).to_be_hidden()
