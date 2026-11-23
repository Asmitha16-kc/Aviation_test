import re
from pages.base_page import BasePage
from utils.config import BASE_URL


class ContactsPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.heading = page.get_by_role("heading", name="Contact Directory")
        self.add_button = page.get_by_role("button", name="Add contact")
        self.add_dialog = page.get_by_role("dialog", name="Add Contact")
        self.edit_dialog = page.get_by_role("dialog", name="Edit Contact")
        self.filters_button = page.get_by_role("button", name="Filters")
        self.filters_heading = page.get_by_role("heading", name="Filters")
        self.close_filters_button = page.get_by_role("button", name="Close filters")
        self.clear_filters_button = page.get_by_role(
            "button", name="Clear all filters"
        )
        self.support_filter = page.get_by_role(
            "checkbox", name="24x7 support only"
        )
        self.inactive_filter = page.get_by_role(
            "checkbox", name="Show inactive contacts"
        )
        self.columns_button = page.get_by_role("button", name="Choose columns")
        self.show_all_columns_button = page.get_by_role("button", name="Show all")

    @property
    def rows(self):
        return self.page.get_by_role("row").filter(
            has=self.page.get_by_role("button", name=re.compile(r"^Actions for "))
        )

    def open(self):
        if self.heading.is_visible():
            return

        dashboard_url = f"{BASE_URL}/dashboard"
        if self.page.url.rstrip("/") != dashboard_url.rstrip("/"):
            self.page.goto(dashboard_url)
        self.page.get_by_role("button", name="Contact Directory").click()
        self.heading.wait_for()

    def add_contact(self, station, name, designation, phone, email):
        self.add_button.click()
        station_dropdown = self.add_dialog.get_by_role(
            "combobox", name="Airport / Station"
        )
        station_dropdown.click()
        station_pattern = re.compile(
            rf"{re.escape(station)}.*4147.*AYJ.*VEAY", re.I
        )
        self.page.get_by_role("option", name=station_pattern).click()
        self.add_dialog.get_by_role("textbox", name="Contact Name").fill(name)
        self.add_dialog.get_by_role("textbox", name="Designation").fill(designation)
        self.add_dialog.get_by_role("textbox", name="Phone").fill(phone)
        self.add_dialog.get_by_role("textbox", name="Email").fill(email)
        self.add_dialog.get_by_role("button", name="Add Contact").click()
        self.add_dialog.wait_for(state="hidden")

    def contact_row(self, phone):
        return self.rows.filter(
            has=self.page.get_by_role("gridcell", name=phone, exact=True)
        )

    def edit_contact(self, name, phone):
        row = self.contact_row(phone)
        row.get_by_role("button", name=f"Actions for {name}").click()
        self.page.get_by_role("menuitem", name="Edit contact").click()
        return self.edit_dialog

    def save_contact(self):
        self.edit_dialog.get_by_role("button", name="Save Changes").click()
        self.edit_dialog.wait_for(state="hidden")

    def set_contact_status(self, name, phone, active):
        action = "Deactivate contact" if active else "Activate contact"
        confirmation = "Deactivate" if active else "Activate"
        row = self.contact_row(phone)
        row.get_by_role("button", name=f"Actions for {name}").click()
        self.page.get_by_role("menuitem", name=action).click()
        dialog = self.page.get_by_role("dialog")
        dialog.get_by_role("button", name=confirmation, exact=True).click()
        dialog.wait_for(state="hidden")

    def open_filters(self):
        self.filters_button.click()

    def close_filters(self):
        self.close_filters_button.click()

    def clear_filters(self):
        if not self.filters_heading.is_visible():
            self.open_filters()
        self.clear_filters_button.click()
        self.close_filters()

    def open_columns(self):
        self.columns_button.click()