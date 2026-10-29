import time
import pytest
from playwright.sync_api import expect
from pages.contacts import ContactsPage

STATION = "Ayodhya AFS"
DESIGNATION = "Test Coordinator"
UPDATED_DESIGNATION = "Senior Test Coordinator"


@pytest.fixture(scope="module")
def created_contact(_super_admin_session):
    contacts = ContactsPage(_super_admin_session)
    contacts.open()

    unique_id = str(time.time_ns() % 1_000_000_000).zfill(9)
    contact = {
        "name": f"Contact Test {unique_id}",
        "phone": f"8{unique_id}",
        "email": f"contact-{unique_id}@example.com",
    }
    contacts.add_contact(
        STATION,
        contact["name"],
        DESIGNATION,
        contact["phone"],
        contact["email"],
    )
    expect(contacts.contact_row(contact["phone"])).to_be_visible()
    return contacts, contact


@pytest.fixture
def contacts_context(created_contact):
    contacts, contact = created_contact
    contacts.open()
    return contacts, contact


def test_add_contact(created_contact):
    contacts, contact = created_contact
    row = contacts.contact_row(contact["phone"])
    expect(row).to_be_visible()
    expect(row).to_contain_text(contact["name"])
    expect(row.get_by_role("gridcell").nth(7)).to_have_text("Active")


def test_edit_contact(contacts_context):
    contacts, contact = contacts_context
    row = contacts.contact_row(contact["phone"])
    edit_dialog = contacts.edit_contact(contact["name"], contact["phone"])
    edit_dialog.get_by_role("textbox", name="Designation").fill(
        UPDATED_DESIGNATION
    )
    support_checkbox = edit_dialog.get_by_role(
        "checkbox", name="24x7 support contact"
    )
    support_checkbox.check()
    contacts.save_contact()
    expect(row.get_by_role("gridcell").nth(3)).to_have_text(UPDATED_DESIGNATION)
    expect(row.get_by_role("gridcell").nth(6)).to_have_text("24x7")


def test_filter_shows_24x7_support_contacts(contacts_context):
    contacts, contact = contacts_context
    row = contacts.contact_row(contact["phone"])
    contacts.open_filters()
    contacts.support_filter.check()
    contacts.close_filters()

    expect(row).to_be_visible()
    expect(row.get_by_role("gridcell").nth(6)).to_have_text("24x7")


def test_show_inactive_filter_does_not_show_active_contacts(contacts_context):
    contacts, contact = contacts_context
    row = contacts.contact_row(contact["phone"])
    expect(row.get_by_role("gridcell").nth(7)).to_have_text("Active")

    contacts.open_filters()
    if not contacts.support_filter.is_checked():
        contacts.support_filter.check()
    contacts.inactive_filter.check()
    contacts.close_filters()
    active_contact_visible = row.is_visible()

    assert not active_contact_visible, (
        "Active contact remained visible when Show inactive contacts was enabled"
    )


def test_hide_and_restore_designation_column(contacts_context):
    contacts, _ = contacts_context
    page = contacts.page
    contacts.open_columns()

    designation_checkbox = page.get_by_role(
        "checkbox", name="Designation", exact=True
    )
    designation_header = page.get_by_role(
        "columnheader", name="Designation", exact=True
    )
    designation_checkbox.uncheck()
    expect(designation_header).not_to_be_visible()
    designation_checkbox.check()
    page.keyboard.press("Escape")
    expect(designation_header).to_be_visible()
