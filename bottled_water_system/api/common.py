import frappe

@frappe.whitelist(allow_guest=True)
def get_genders():
    genders = frappe.get_all("Gender")
    return genders





@frappe.whitelist()
def get_customer() :
    current_user = frappe.session.user
    customer_list = frappe.db.sql("""
        SELECT parent 
        FROM `tabPortal User` 
        WHERE user = %s
        LIMIT 1
    """, (current_user,), as_dict=True)
    if not customer_list:
        frappe.throw("No customer found for the current user.")
    customer = customer_list[0].parent

    return customer