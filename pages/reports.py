import re
from urllib.parse import urlsplit

from pages.base_page import BasePage
from utils.config import BASE_URL


class ReportsPage(BasePage):
    def _open_report(self, name, route):
        current_path = urlsplit(self.page.url).path.rstrip("/")
        if current_path == route:
            return

        dashboard_url = f"{BASE_URL.rstrip('/')}/dashboard"
        dashboard_path = urlsplit(dashboard_url).path.rstrip("/")
        if current_path != dashboard_path and not current_path.startswith("/reports/"):
            self.page.goto(dashboard_url)
            current_path = dashboard_path

        if current_path == dashboard_path:
            self.page.get_by_role("button", name="Reports").click()
        self.page.get_by_role("button", name=name).click()

    def open_fdv_report(self):
        self._open_report("FDV Report", "/reports/fdv")
        self.page.locator(".MuiDataGrid-row").first.wait_for(state="visible")

    def open_dispatch_report(self):
        self._open_report("Dispatch Report", "/reports/dispatch")
        self.page.locator(".MuiDataGrid-row").first.wait_for(state="visible")

    def open_soa_report(self):
        self._open_report("SOA Report", "/reports/soa")

    def select_customer_option(self, customer):
        option = self.page.get_by_role("option", name=customer, exact=True)
        if not option.is_visible():
            self.page.locator('[role="combobox"]').first.click()
        option.click()

    def set_date_range(self, start_date, end_date):
        self.page.get_by_role("textbox", name="From date").fill(start_date)
        self.page.get_by_role("textbox", name="To date").fill(end_date)

    def open_columns(self):
        self.page.get_by_role("button", name="Choose columns").click()

    def hide_columns(self, columns):
        for column in columns:
            checkbox = self.page.get_by_role(
                "checkbox", name=column, exact=True
            )
            if checkbox.is_checked():
                checkbox.uncheck()
        self.page.keyboard.press("Escape")

    def open_filters(self):
        close_button = self.page.get_by_role(
            "button", name="Close filters", exact=True
        )
        if not close_button.is_visible():
            self.page.get_by_role("button", name="Filters", exact=True).click()

    def close_filters(self):
        close_button = self.page.get_by_role(
            "button", name="Close filters", exact=True
        )
        if close_button.is_visible():
            close_button.click()

    def select_plant(self, plant):
        self.page.get_by_role("textbox", name="Plant").click()
        self.page.get_by_role("option", name=plant, exact=True).click()
        self.close_filters()

    def select_all_plants(self):
        self.page.get_by_role("textbox", name="Plant").click()
        self.page.get_by_role("button", name="All plants", exact=True).click()
        self.close_filters()

    def download_pdf(self):
        self.page.get_by_role(
            "button", name=re.compile(r"^Download(?: \(\d+ selected\))?$")
        ).click()
        with self.page.expect_download() as download_info:
            self.page.get_by_role("menuitem", name="Download as PDF").click()
        return download_info.value
