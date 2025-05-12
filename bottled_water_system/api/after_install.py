


import frappe


@frappe.whitelist()
def create_role() :
    if not frappe.db.exists("Role", "Water Delivery Boy") :
        role_doc = frappe.new_doc('Role')
        role_doc.role_name = 'Water Delivery Boy'
        role_doc.desk_access = 1
        role_doc.insert()



