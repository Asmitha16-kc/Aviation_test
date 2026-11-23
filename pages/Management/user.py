import re

from pages.Management.org_access_control import OrgDirectoryPage
from playwright.sync_api import expect


class UserManagementPage(OrgDirectoryPage):
    def open(self, organization="BPCL"):
        heading = self.page.get_by_role(
            "heading", name="User Management", exact=True
        )
        if not heading.is_visible():
            self.page.get_by_role("button", name="Users", exact=True).click()
            user_directory = self.page.get_by_role(
                "button", name="User directory", exact=True
            )
            if user_directory.is_visible():
                user_directory.click()
            expect(heading).to_be_visible()
        self.select_organization(organization)

    def user_row(self, username):
        return self.page.get_by_role(
            "row", name=re.compile(re.escape(username))
        )

    def open_user_actions(self, username):
        row = self.user_row(username)
        expect(row).to_be_visible()
        row.get_by_role("gridcell").last.hover()
        actions = self.page.get_by_role(
            "button", name=f"Actions for {username}", exact=True
        )
        expect(actions).to_be_visible()
        actions.click()

    def edit_user(self, username, updated_username):
        self.open_user_actions(username)
        self.page.get_by_role("menuitem", name="Edit user", exact=True).click()
        self.page.get_by_role("textbox", name="User Name *").fill(updated_username)
        self.page.get_by_role("button", name="Save Changes", exact=True).click()

    def user_is_active(self, username):
        self.open_user_actions(username)
        deactivate = self.page.get_by_role(
            "menuitem", name="Deactivate user", exact=True
        )
        activate = self.page.get_by_role(
            "menuitem", name="Activate user", exact=True
        )
        try:
            is_active = deactivate.is_visible()
            is_inactive = activate.is_visible()
            assert is_active != is_inactive, (
                f"Expected exactly one activation action for {username!r}"
            )
            return is_active
        finally:
            self.page.keyboard.press("Escape")

    def deactivate_user(self, username):
        self.open_user_actions(username)
        self.page.get_by_role(
            "menuitem", name="Deactivate user", exact=True
        ).click()
        self.page.get_by_role("button", name="Deactivate", exact=True).click()

    def activate_user(self, username, confirm=True):
        self.open_user_actions(username)
        self.page.get_by_role(
            "menuitem", name="Activate user", exact=True
        ).click()
        button_name = "Activate" if confirm else "Cancel"
        self.page.get_by_role("button", name=button_name, exact=True).click()

    def set_user_active(self, username, active):
        self.open_user_actions(username)
        action_name = "Activate user" if active else "Deactivate user"
        action = self.page.get_by_role("menuitem", name=action_name, exact=True)
        if not action.is_visible():
            opposite_action = (
                "Deactivate user" if active else "Activate user"
            )
            expect(
                self.page.get_by_role(
                    "menuitem", name=opposite_action, exact=True
                )
            ).to_be_visible()
            self.page.keyboard.press("Escape")
            return

        action.click()
        if active:
            self.page.get_by_role("button", name="Activate", exact=True).click()
        else:
            self.page.get_by_role("button", name="Deactivate", exact=True).click()
