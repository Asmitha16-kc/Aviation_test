import re
from urllib.parse import urlsplit

from pages.base_page import BasePage
from playwright.sync_api import expect
from utils.config import BASE_URL


class OrgDirectoryPage(BasePage):
    def open(self):
        self.open_organization_directory()
        self.page.wait_for_load_state("networkidle")
        self.page.get_by_role(
            "heading", name="Organizations", exact=True
        ).wait_for()

    def organization_actions(self, organization):
        return self.page.get_by_role("button", name=f"Actions for {organization}")

    def organization_row(self, organization):
        return self.page.get_by_role(
            "row", name=re.compile(rf"^{re.escape(organization)}(?:\s|$)")
        )

    def set_organization_enabled(self, organization, enabled):
        row = self.organization_row(organization)
        current_status = row.get_by_role("gridcell").nth(5).inner_text().strip()
        currently_enabled = current_status == "Active"
        if currently_enabled == enabled:
            return

        action = "Enable organization" if enabled else "Disable organization"
        confirmation = "Enable" if enabled else "Disable"
        self.open_organization_menu(organization)
        self.page.get_by_role("menuitem", name=action, exact=True).click()
        dialog = self.page.get_by_role("dialog")
        dialog.get_by_role("button", name=confirmation, exact=True).click()
        dialog.wait_for(state="hidden")
        expect(row.get_by_role("gridcell").nth(5)).to_have_text(
            "Active" if enabled else "Disabled"
        )

    def open_organization_directory(self):
        directory_url = f"{BASE_URL}/admin/organizations"
        if (
            urlsplit(self.page.url).path.rstrip("/")
            != urlsplit(directory_url).path.rstrip("/")
        ):
            self.page.goto(directory_url)

    def open_organization_menu(self, organization):
        self.open_organization_directory()
        self.page.keyboard.press("Escape")
        self.organization_actions(organization).click()

    def view_users(self, organization):
        if urlsplit(self.page.url).path.rstrip("/") == "/users":
            selector = self.page.get_by_role("combobox", name="Organization")
            if selector.count() and selector.inner_text().strip() == organization:
                return
        self.open_organization_menu(organization)
        self.page.get_by_text("View users", exact=True).click()

    def open_add_user_form(self):
        self.page.get_by_role("button", name="Add user").click()

    def fill_add_user_identity(self, username, email, mobile, start_date, end_date):
        self.page.get_by_role("textbox", name="User Name *").fill(username)
        self.page.get_by_role("textbox", name="Email ID *").fill(email)
        self.page.get_by_role("textbox", name="Mobile Number *").fill(mobile)
        start_field = self.page.get_by_role("textbox", name="Start Date *")
        start_field.fill(start_date)
        start_field.press("Tab")
        end_field = self.page.get_by_role("textbox", name="End Date *")
        end_field.fill(end_date)
        end_field.press("Tab")

    def select_new_user_access(self, role):
        self.select_new_user_role(role)
        self.page.get_by_role("textbox", name="Mobile Number *").click()
        self.page.get_by_test_id("KeyboardArrowDownIcon").last.click(force=True)
        self.page.get_by_role("checkbox", name="Select all plants").set_checked(False)
        self.page.get_by_role("option", name="- Delhi (T-3) Delhi").get_by_role("checkbox").check()
        self.page.keyboard.press("Escape")

    def select_new_user_role(self, role):
        self._select_add_user_option(role)

    def _select_add_user_option(self, option_name):
        option = self.page.get_by_role("option", name=option_name, exact=True)
        comboboxes = self.page.get_by_role("combobox")
        for index in range(comboboxes.count()):
            combobox = comboboxes.nth(index)
            if not combobox.is_visible():
                continue
            combobox.click()
            if option.is_visible():
                option.click()
                self.page.keyboard.press("Tab")
                return
            self.page.keyboard.press("Escape")
        raise AssertionError(f"Could not open the selector for option: {option_name}")

    def submit_add_user_form(self):
        self.page.get_by_role("button", name="Invite User").click()
        self.page.get_by_role("button", name="Done").click()

    def open_configure_roles(self, organization):
        self.open_organization_menu(organization)
        self.page.get_by_role("menuitem", name="Configure roles").click()

    def select_organization(self, organization):
        selector = self.page.get_by_role("combobox").first
        expect(selector).to_be_enabled()
        if selector.inner_text().strip() == organization:
            return
        selector.click()
        option = self.page.get_by_role("option", name=organization, exact=True)
        expect(option).to_be_visible()
        option.click()

    def role_actions(self, role):
        return self.page.get_by_role("button", name=f"Actions for {role}")

    def role_button(self, role):
        name = re.compile(rf"^{re.escape(role)}(?:\s|$)")
        return self.page.get_by_role("button", name=name)

    def open_categories_tab(self):
        self.page.get_by_role("tab", name="Customer categories").click()

    def open_roles_tab(self):
        self.page.get_by_role("tab", name="Roles & permissions").click()

    def category_actions(self, category):
        return self.page.get_by_role("button", name=f"Actions for {category}")

    def category_is_locked(self, category):
        self.category_actions(category).click()
        is_locked = self.page.get_by_role("menuitem", name="Unlock", exact=True).count() > 0
        self.page.keyboard.press("Escape")
        return is_locked

    def set_category_locked(self, category, locked):
        if self.category_is_locked(category) == locked:
            return
        self.category_actions(category).click()
        action_name = "Lock Protect from deletion" if locked else "Unlock"
        self.page.get_by_role("menuitem", name=action_name, exact=True).click()

    def category_checkbox(self, category, module):
        row_name = re.compile(rf"^{re.escape(category)}(?:\s|$)")
        return self.page.get_by_role("row", name=row_name).get_by_label(module)

    def save_changes(self):
        self.page.get_by_role("button", name="Save changes").click()
        confirmation = self.page.get_by_role("button", name="Remove and save")
        if confirmation.count() and confirmation.is_visible():
            confirmation.click()
