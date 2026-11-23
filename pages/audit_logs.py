import re
from pages.base_page import BasePage
from utils.config import BASE_URL


class AuditLogsPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.heading = page.get_by_role("heading", name="Audit Logs")
        self.search_box = page.get_by_role("textbox", name="Search by actor")
        self.clear_search_btn = page.get_by_role("button", name="Clear search")
        self.action_filter = page.get_by_role("combobox", name="Action")
        self.organization_filter = page.get_by_role("combobox", name="Organization")
        self.entity_filter = page.get_by_role("combobox", name="Entity")
        self.filters_btn = page.get_by_role("button", name="Filters")
        self.close_filters_btn = page.get_by_role("button", name="Close filters")
        self.clear_all_filters_btn = page.get_by_role("button", name="Clear all filters")
        self.from_date = page.get_by_role("textbox", name="From")
        self.to_date = page.get_by_role("textbox", name="To")
        self.columns_btn = page.get_by_role("button", name="Choose columns")
        self.show_all_btn = page.get_by_role("button", name="Show all")
        self.view_buttons = page.get_by_role("button", name="View")
        self.popup = page.get_by_role("dialog")
        self.close_btn = page.get_by_role("button", name="Close")
        # data rows = rows that contain a View button (skips the header row)
        self.rows = page.get_by_role("row").filter(
            has=page.get_by_role("button", name="View")
        )

    # ---------- open ----------
    def open(self):
        if self.heading.is_visible():
            return

        dashboard_url = f"{BASE_URL}/dashboard"
        if self.page.url.rstrip("/") != dashboard_url.rstrip("/"):
            self.page.goto(dashboard_url)
        menu = self.page.get_by_role("button", name="Audit Logs").or_(
            self.page.get_by_role("link", name="Audit Logs")
        )
        menu.first.click()
        self.heading.wait_for()

    # ---------- search ----------
    def search_by_actor(self, name):
        self.search_box.fill(name)

    def clear_search(self):
        self.clear_search_btn.click()

    # ---------- view details ----------
    def open_first_log(self):
        self.view_buttons.first.click()

    def close_popup(self):
        self.close_btn.click()

    # ---------- dropdowns (tries several ways to find the closed dropdown) ----------
    def _choose(self, dropdown, option):
        dropdown.click()
        exact = re.compile(f"^{re.escape(option)}$", re.I)
        self.page.get_by_role("option", name=exact).click()

    def select_action(self, action):
        self._choose(self.action_filter, action)

    def open_filters(self):
        self.filters_btn.click()

    def select_organization(self, org):
        self._choose(self.organization_filter, org)

    def select_entity(self, entity):
        self._choose(self.entity_filter, entity)

    def set_date_range(self, start_date, end_date):
        self.from_date.fill(start_date)
        self.to_date.fill(end_date)

    def clear_all_filters(self):
        self.clear_all_filters_btn.click()

    # ---------- columns ----------
    def open_columns(self):
        self.columns_btn.click()

    def close_columns(self):
        self.page.keyboard.press("Escape")

    def column_checkbox(self, column):
        return self.page.get_by_role("checkbox", name=column, exact=True)

    def column_header(self, column):
        return self.page.get_by_role(
            "columnheader", name=re.compile(re.escape(column), re.I)
        )

    def hide_column(self, column):
        self.column_checkbox(column).uncheck()

    def show_all_columns(self):
        self.show_all_btn.click()