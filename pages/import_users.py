from pathlib import Path
import re

from pages.base_page import BasePage
from playwright.sync_api import expect


class ImportUsersPage(BasePage):
    def open(self):
        user_management_heading = self.page.get_by_role(
            "heading", name="User Management", exact=True
        )
        if not user_management_heading.is_visible():
            self.page.get_by_role("button", name="Users", exact=True).click()
            self.page.get_by_role(
                "button", name="User directory", exact=True
            ).click()
            expect(user_management_heading).to_be_visible()

        self.page.get_by_role(
            "button", name=re.compile(r"^Import Users$", re.I)
        ).click()

    def upload_csv(self, filename):
        csv_path = Path(__file__).resolve().parents[1] / filename
        self.page.locator('input[type="file"]').set_input_files(str(csv_path))
