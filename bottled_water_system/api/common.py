import frappe

@frappe.whitelist(allow_guest=True)
def get_genders():
    genders = frappe.get_all("Gender")
    return genders

