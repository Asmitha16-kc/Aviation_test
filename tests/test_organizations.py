import re
from datetime import date, timedelta

import pytest
from playwright.sync_api import expect

from pages.Management.org_access_control import OrgDirectoryPage
from utils.config import BASE_URL


ORG = "BPCL"
OTHER_ORG = "SNV AVIATION PRIVATE LTD"
USER = "user1234"
NEW_USER = "testing user21121"
NEW_USER_EMAIL = "testuser12@gmail.com"
NEW_USER_MOBILE = "9876543232"
NEW_USER_ROLE = "Operations"
ROLE = "Finance"
CATEGORY = "Scheduled"
DISABLED_ORG = "SNV AVIATION PRIVATE LTD"


@pytest.fixture(scope="module")
def org_page(_super_admin_session):
	organization_page = OrgDirectoryPage(_super_admin_session)
	organization_page.open()
	return organization_page


@pytest.fixture(scope="module")
def roles_page(org_page):
	org_page.open_configure_roles(OTHER_ORG)
	return org_page


def test_organization_menu_shows_role_and_edit_actions(org_page):
	org_page.open_organization_menu(ORG)
	expect(org_page.page.get_by_role("menuitem", name="Configure roles")).to_be_visible()
	expect(org_page.page.get_by_role("menuitem", name="Edit organization")).to_be_visible()


def test_user_directory_add_user(org_page):
	org_page.view_users(ORG)
	new_user_row = org_page.page.get_by_role("row", name=re.compile(re.escape(NEW_USER)))
	user_already_exists = new_user_row.count() > 0
	start_date = (date.today() + timedelta(days=1)).isoformat()
	end_date = (date.today() + timedelta(days=10)).isoformat()
	org_page.open_add_user_form()
	org_page.fill_add_user_identity(
		NEW_USER,
		NEW_USER_EMAIL,
		NEW_USER_MOBILE,
		start_date,
		end_date,
	)
	expect(org_page.page.get_by_role("textbox", name="Start Date *")).to_have_value(start_date)
	expect(org_page.page.get_by_role("textbox", name="End Date *")).to_have_value(end_date)
	expect(org_page.page.get_by_role("button", name="Invite User")).to_be_visible()
	if user_already_exists:
		org_page.select_new_user_role(NEW_USER_ROLE)
		cancel_button = org_page.page.get_by_role("button", name="Cancel")
		if cancel_button.count():
			cancel_button.click()
		else:
			org_page.page.keyboard.press("Escape")
	else:
		org_page.select_new_user_access(NEW_USER_ROLE)
		org_page.submit_add_user_form()
		new_user_row = org_page.page.get_by_role("row", name=re.compile(re.escape(NEW_USER)))
		expect(new_user_row).to_be_visible()

	row = org_page.page.get_by_role("row", name=re.compile(re.escape(USER)))
	expect(row).to_be_visible()
	row.get_by_role("gridcell").last.hover()
	org_page.page.get_by_role("button", name=f"Actions for {USER}").click()
	org_page.page.get_by_text("Edit user", exact=True).click()
	expect(org_page.page.get_by_role("textbox", name="User Name *")).to_be_visible()
	cancel_button = org_page.page.get_by_role("button", name="Cancel")
	if cancel_button.count():
		cancel_button.click()
	else:
		org_page.page.keyboard.press("Escape")


def test_roles_for_selected_organization_are_visible(roles_page):
	expect(roles_page.role_button("Customer Administrator")).to_be_visible()


def test_dashboard_permission_can_be_unchecked_and_checked(roles_page):
	roles_page.role_button("Customer Administrator").click()
	dashboard_permission = roles_page.page.get_by_role(
		"checkbox", name="Read access for Dashboard"
	)
	initial_state = dashboard_permission.is_checked()
	save_button = roles_page.page.get_by_role("button", name="Save changes")

	try:
		dashboard_permission.set_checked(not initial_state)
		roles_page.save_changes()
		if initial_state:
			expect(dashboard_permission).not_to_be_checked()
		else:
			expect(dashboard_permission).to_be_checked()

		dashboard_permission.set_checked(initial_state)
		roles_page.save_changes()
		if initial_state:
			expect(dashboard_permission).to_be_checked()
		else:
			expect(dashboard_permission).not_to_be_checked()
	finally:
		if dashboard_permission.is_checked() != initial_state:
			dashboard_permission.set_checked(initial_state)
			if save_button.is_enabled():
				roles_page.save_changes()


def test_lock_action_is_available(roles_page):
	roles_page.role_actions(ROLE).click()
	lock_action = roles_page.page.get_by_role("menuitem", name="Lock Protect from deletion")
	unlock_action = roles_page.page.get_by_role("menuitem", name="Unlock", exact=True)
	assert lock_action.count() + unlock_action.count() == 1
	roles_page.page.keyboard.press("Escape")


def test_scheduled_category_module_workflow(roles_page):
	roles_page.open_categories_tab()
	roles_page.category_actions(CATEGORY).click()
	unlock_action = roles_page.page.get_by_role("menuitem", name="Unlock", exact=True)
	was_locked = unlock_action.count() > 0
	if was_locked:
		unlock_action.click()
	else:
		roles_page.page.keyboard.press("Escape")
	domestic = roles_page.category_checkbox(CATEGORY, "Domestic")
	international = roles_page.category_checkbox(CATEGORY, "International")
	fuel_requests = roles_page.page.get_by_role(
		"checkbox", name=f"Fuel Requests for {CATEGORY}"
	)
	was_domestic_checked = domestic.is_checked()
	was_international_checked = international.is_checked()
	was_fuel_requests_checked = fuel_requests.is_checked()
	save_button = roles_page.page.get_by_role("button", name="Save changes")
	try:
		if not domestic.is_checked():
			domestic.check()
			roles_page.save_changes()
		if not international.is_checked():
			international.check()
			roles_page.save_changes()
		expect(domestic).to_be_checked()
		expect(international).to_be_checked()

		domestic.uncheck()
		international.uncheck()
		expect(roles_page.page.get_by_text("Choose at least one", exact=True)).to_be_visible()
		expect(save_button).to_be_disabled()

		domestic.check()
		roles_page.save_changes()
		expect(domestic).to_be_checked()
		expect(international).not_to_be_checked()

		if fuel_requests.is_checked():
			fuel_requests.uncheck()
			roles_page.save_changes()
		expect(fuel_requests).not_to_be_checked()

		roles_page.open_roles_tab()
		roles_page.role_button("Customer Administrator").click()
		read_access = roles_page.page.get_by_role(
			"checkbox", name="Read access for Fuel Requests"
		)
		if read_access.count():
			expect(read_access).to_be_disabled()
		else:
			expect(read_access).to_have_count(0)

		roles_page.open_categories_tab()
		fuel_requests = roles_page.page.get_by_role(
			"checkbox", name=f"Fuel Requests for {CATEGORY}"
		)
		fuel_requests.check()
		roles_page.save_changes()
		expect(fuel_requests).to_be_checked()
	finally:
		roles_page.open_categories_tab()
		restore_domestic = was_domestic_checked or not was_international_checked
		if domestic.is_checked() != restore_domestic:
			domestic.set_checked(restore_domestic)
		if international.is_checked() != was_international_checked:
			international.set_checked(was_international_checked)
		if fuel_requests.is_checked() != was_fuel_requests_checked:
			fuel_requests.set_checked(was_fuel_requests_checked)
		if save_button.is_enabled():
			roles_page.save_changes()
		if was_locked:
			roles_page.category_actions(CATEGORY).click()
			roles_page.page.get_by_role(
				"menuitem", name="Lock Protect from deletion", exact=True
			).click()


def test_add_category_dialog_can_be_cancelled(roles_page):
	roles_page.open_categories_tab()
	roles_page.page.get_by_role("button", name="Add category").click()
	expect(roles_page.page.get_by_role("button", name="Cancel")).to_be_visible()
	roles_page.page.get_by_role("button", name="Cancel").click()


def test_organization_category_assignment_can_be_saved(org_page):
	org_page.open_organization_menu(DISABLED_ORG)
	org_page.page.get_by_role("menuitem", name="Edit organization").click()
	selector = org_page.page.get_by_role("combobox").first
	selector.click()
	expect(org_page.page.get_by_role("option", name=CATEGORY, exact=True)).to_be_visible()
	org_page.page.get_by_role("option", name="Non-Scheduled").click()
	selector.click()
	org_page.page.get_by_role("option", name="Scheduled", exact=True).click()
	org_page.page.get_by_role("button", name="Save Changes").click()
	expect(
		org_page.page.get_by_role("heading", name="Organizations", exact=True)
	).to_be_visible()
	expect(
		org_page.page.get_by_role("row", name=re.compile(re.escape(DISABLED_ORG)))
	).to_be_visible()


def test_disable_and_enable_organization_after_user_directory(org_page):
	org_page.view_users(ORG)
	expect(
		org_page.page.get_by_role("heading", name="User Management", exact=True)
	).to_be_visible()

	org_page.open()
	row = org_page.organization_row(DISABLED_ORG)
	expect(row).to_be_visible()
	was_enabled = row.get_by_role("gridcell").nth(5).inner_text().strip() == "Active"

	try:
		org_page.set_organization_enabled(DISABLED_ORG, enabled=False)
		org_page.set_organization_enabled(DISABLED_ORG, enabled=True)
	finally:
		org_page.set_organization_enabled(DISABLED_ORG, enabled=was_enabled)

	expect(row.get_by_role("gridcell").nth(5)).to_have_text(
		"Active" if was_enabled else "Disabled"
	)
