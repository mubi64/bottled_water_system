import frappe

@frappe.whitelist(allow_guest=True)
def get_genders():
    genders = frappe.get_all("Gender", pluck='name')
    return genders


@frappe.whitelist()
def get_countries() :
    countries = frappe.get_all("Country")
    return countries


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




@frappe.whitelist()
def get_customer_info() :
    current_user = frappe.session.user
    usr_doc = frappe.get_doc('User',current_user)
    return {'full_name':usr_doc.full_name, 'email':current_user, 'date_of_birth':usr_doc.birth_date, 'gender': usr_doc.gender, 'number':usr_doc.mobile_no }

