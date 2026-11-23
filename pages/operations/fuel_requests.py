import re
from playwright.sync_api import expect
from pages.base_page import BasePage
from utils.config import BASE_URL

TABS = [
    "All", "Draft", "Pending review", "Accepted", "Declined",
    "Modification required", "Expired", "Cancelled",
]


class FuelRequestsPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.sidebar_link = page.get_by_role("button", name="Fuel Requests")
        self.new_request_btn = page.get_by_role("button", name="New Fuel Request")
        self.flight_number = page.get_by_role("textbox", name="Flight Number *")
        self.aircraft_reg = page.get_by_role("textbox", name="Aircraft Reg. No. *")
        self.submit_btn = page.get_by_role("button", name="Submit Fuel Request")
        self.confirm_btn = page.get_by_role("button", name="Confirm & Proceed")
        self.actions_buttons = page.get_by_role(
            "button", name=re.compile(r"Actions for REQ-\d{8}-\d+")
        )
        self.next_page_btn = page.get_by_role("button", name="Go to next page")
        self.prev_page_btn = page.get_by_role("button", name="Go to previous page")

    def open(self):
        self.page.goto(f"{BASE_URL}/dashboard")
        self.sidebar_link.click()

    def tab(self, name):
        return self.page.get_by_role("tab", name=name)

    def open_tab(self, name):
        self.tab(name).click()

    def create_request(self, flight_no, aircraft_reg):
        self.new_request_btn.click()
        self.flight_number.fill(flight_no)
        self.aircraft_reg.fill(aircraft_reg)
        self.submit_btn.click()
        self.confirm_btn.click()

    def open_first_actions(self):
        expect(self.actions_buttons.first).to_be_visible(timeout=60000)
        self.actions_buttons.first.click()

    def go_next_page(self):
        self.next_page_btn.click()
