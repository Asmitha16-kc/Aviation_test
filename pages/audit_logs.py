import re
from pages.base_page import BasePage
from utils.config import BASE_URL


class AuditLogsPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.heading = page.get_by_role(
            "heading", name=re.compile(r"^Audit Logs$", re.I)
        )
        self.search_box = page.get_by_role(
            "textbox", name=re.compile(r"Search by actor", re.I)
        )
        self.clear_search_btn = page.get_by_role(
            "button", name=re.compile(r"Clear search", re.I)
        )
        self.action_filter = page.get_by_role(
            "combobox", name=re.compile(r"^Action(?:\s+.*)?$", re.I)
        )
        self.organization_filter = page.get_by_role(
            "combobox", name=re.compile(r"^Organization$", re.I)
        )
        self.entity_filter = page.get_by_role(
            "combobox", name=re.compile(r"^Entity$", re.I)
        )
        self.filters_btn = page.get_by_role(
            "button", name=re.compile(r"Filters?", re.I)
        )
        self.close_filters_btn = page.get_by_role(
            "button", name=re.compile(r"Close filters?", re.I)
        )
        self.clear_all_filters_btn = page.get_by_role(
            "button", name=re.compile(r"Clear all filters?", re.I)
        )
        self.from_date = page.get_by_role(
            "textbox", name=re.compile(r"^From$", re.I)
        )
        self.to_date = page.get_by_role(
            "textbox", name=re.compile(r"^To$", re.I)
        )
        self.columns_btn = page.get_by_role(
            "button", name=re.compile(r"Choose columns?", re.I)
        )
        self.show_all_btn = page.get_by_role(
            "button", name=re.compile(r"Show all", re.I)
        )
        self.view_buttons = page.get_by_role(
            "button", name=re.compile(r"^View$|^Details?$", re.I)
        )
        self.popup = page.get_by_role("dialog")
        self.close_btn = self.popup.get_by_label("Close", exact=True)
        # data rows = rows that contain an action button, regardless of button text
        self.rows = page.get_by_role("row").filter(
            has=page.locator("button, [role='button'], a").filter(
                has_text=re.compile(r"View|Details|Open|Actions", re.I)
            )
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
        self.search_box.press("Enter")

    def clear_search(self):
        if self.clear_search_btn.is_visible():
            self.clear_search_btn.click()
        else:
            self.search_box.fill("")

    # ---------- view details ----------
    def open_first_log(self):
        self.view_buttons.first.click()

    def close_popup(self):
        if self.popup.is_visible():
            self.close_btn.click()
            self.popup.wait_for(state="hidden")

    # ---------- dropdowns (tries several ways to find the closed dropdown) ----------
    def _choose(self, dropdown, option):
        dropdown.click()
        exact = re.compile(f"^{re.escape(option)}$", re.I)
        candidates = [
            self.page.get_by_role("option", name=exact),
            self.page.get_by_role("menuitem", name=exact),
            self.page.get_by_text(option, exact=True),
            self.page.get_by_text(re.compile(re.escape(option), re.I)),
        ]
        for candidate in candidates:
            if candidate.count():
                candidate.first.click()
                return
        raise AssertionError(f"Could not find option {option!r} in the dropdown")

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
        self.page.keyboard.press("Tab")

    def clear_all_filters(self):
        if self.clear_all_filters_btn.is_visible():
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