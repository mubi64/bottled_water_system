import frappe
from datetime import date
from bottled_water_system.api.common import (get_customer, get_company_currency, get_item_image)
from erpnext.controllers.accounts_controller import get_item_details


@frappe.whitelist()
def get_packages():
    packages = frappe.get_all("Bottle Package", 
        filters={"enabled":1},
        fields=["name", "package_name", "bottle_quantity", "item", "description"],
        order_by="display_order")

    for package in packages:
        itm_doc = frappe.get_doc('Item', package.get("item"))

        price = frappe.db.get_value("Item Price", 
            {"item_code": package.get("item")}, 
            "price_list_rate")
        currency = frappe.db.get_value("Item Price", 
            {"item_code": package.get("item")}, 
            "currency")
        
        if not currency :
            currency = get_company_currency()

        package["price"] = int(price) if price else 0
        package["currency"] = currency
        package['image'] = itm_doc.image

    return packages



@frappe.whitelist()
def package_purchase(bottle_packages):
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

    company = frappe.defaults.get_user_default("company")
    if not company:
        frappe.throw("No default company set for the current user.")

    company_currency = frappe.db.get_value("Company", company, "default_currency") or "PKR"

    selling_price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list") or "Standard Selling"


    sales_invoice = frappe.new_doc("Sales Invoice")
    sales_invoice.company = company
    sales_invoice.currency = company_currency 
    sales_invoice.customer = customer_name

    cust_pakage_purchase = []


    for row in bottle_packages :

        package_doc = frappe.get_doc("Bottle Package", row['bottle_package'])

        new_purchase = frappe.new_doc("Customer Package Purchase")
        new_purchase.customer = customer_name
        new_purchase.bottle_package = row['bottle_package']
        new_purchase.purchase_date = date.today()
        new_purchase.package_quantity = row['qty']
        new_purchase.total_bottles = package_doc.bottle_quantity * row['qty']
        new_purchase.bottles_remaining = package_doc.bottle_quantity * row['qty']
        new_purchase.insert(ignore_permissions=True)
        cust_pakage_purchase.append(new_purchase.name)
        
        item_details = get_item_details({
            "item_code": package_doc.item,
            "qty": row['qty'],
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
        
        sales_invoice.append("items", item_details)


    sales_invoice.insert(ignore_permissions=True)
    frappe.db.commit()

    if cust_pakage_purchase :
        for x in cust_pakage_purchase :
            frappe.db.set_value('Customer Package Purchase', x, 'sales_invoice', sales_invoice.name)

    return {'sales_invoice': sales_invoice.name}



@frappe.whitelist()
def get_customer_package_purchases() :

    customer = get_customer()

    cust_package_purchases_list = frappe.get_all('Customer Package Purchase',
                                                 filters = {
                                                     'customer' : customer ,
                                                     'status' : 'Active'
                                                 },
                                                 fields = ['*']
                                                 )
    if cust_package_purchases_list :
        for row in cust_package_purchases_list :
            row['image'] = get_item_image(row.item)


        return cust_package_purchases_list




@frappe.whitelist()
def get_water_bottle_product() :
    water_bottle_product_list = frappe.get_all('Water Bottle Product',fields=['*'])
    company_currency = get_company_currency()
    if water_bottle_product_list :
        for row in water_bottle_product_list :
            row['currency'] = company_currency
            row['image'] = get_item_image(row.item)

    return water_bottle_product_list



