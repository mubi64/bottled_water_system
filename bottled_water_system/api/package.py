import frappe
from datetime import date
from erpnext.controllers.accounts_controller import get_item_details


@frappe.whitelist()
def get_packages():
    packages = frappe.get_all("Bottle Package", 
        filters={"enabled":1},
        fields=["name", "package_name", "bottle_quantity", "item"],
        order_by="display_order")

    for package in packages:
        price = frappe.db.get_value("Item Price", 
            {"item_code": package.get("item")}, 
            "price_list_rate")

        package["price"] = int(price) if price else 0
    return packages

@frappe.whitelist()
def package_purchase(bottle_package):
    current_user = frappe.session.user

    customer = frappe.db.sql("""
        SELECT parent 
        FROM `tabPortal User` 
        WHERE user = %s
        LIMIT 1
    """, (current_user,), as_dict=True)

    if not customer:
        frappe.throw("No customer found for the current user.")

    customer_name = customer[0].parent

    package_doc = frappe.get_doc("Bottle Package", bottle_package)

    new_purchase = frappe.new_doc("Customer Package Purchase")
    new_purchase.customer = customer_name
    new_purchase.bottle_package = bottle_package
    new_purchase.purchase_date = date.today()
    new_purchase.bottles_remaining = package_doc.bottle_quantity
    new_purchase.insert(ignore_permissions=True)
    
    company = frappe.defaults.get_user_default("company")
    if not company:
        frappe.throw("No default company set for the current user.")

    company_currency = frappe.db.get_value("Company", company, "default_currency") or "PKR"

    selling_price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list") or "Standard Selling"


    item_details = get_item_details({
        "item_code": package_doc.item,
        "qty": 1,
        "doctype": "Sales Invoice",
        "customer": customer_name,
        "company": company,
        "currency": company_currency
    })

     # Fallback: Manually fetch price if not returned by get_item_details
    if not item_details.get("rate") or item_details["rate"] == 0:
        price = frappe.db.get_value("Item Price", {
            "item_code": package_doc.item,
            "price_list": selling_price_list,
            "currency": company_currency
        }, "price_list_rate")

        if not price:
            frappe.throw(f"No Item Price found for {package_doc.item} in price list {selling_price_list} with currency {company_currency}.")

        item_details["rate"] = price
        item_details["price_list_rate"] = price

    sales_invoice = frappe.new_doc("Sales Invoice")
    sales_invoice.company = company
    sales_invoice.currency = company_currency 
    sales_invoice.customer = customer_name
    sales_invoice.append("items", item_details)
    sales_invoice.insert(ignore_permissions=True)

    frappe.db.commit()



    return f"Package '{bottle_package}' purchased and invoiced successfully for customer '{customer_name}'."



