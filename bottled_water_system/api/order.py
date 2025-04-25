
import frappe

from bottled_water_system.api.common import get_customer



@frappe.whitelist()
def place_water_order(package_name , bottle_quantity, delivery_date, address) :


    # current_user = frappe.session.user
    # customer_list = frappe.db.sql("""
    #     SELECT parent 
    #     FROM `tabPortal User` 
    #     WHERE user = %s
    #     LIMIT 1
    # """, (current_user,), as_dict=True)
    # if not customer_list:
    #     frappe.throw("No customer found for the current user.")
    # customer = customer_list[0].parent

    customer = get_customer()

    if delivery_date < frappe.utils.today() :
        return {'message':'Delivery Date must be in future dates', 'status':'failed'}
    
    remaining_balance = frappe.db.get_value('Customer Package Purchase', package_name, 'bottles_remaining')

    if remaining_balance < bottle_quantity :
        return {'message':'Your remaining balance from package purchase is less than ordered quantity', 'status':'failed'}


    available = check_available_qty(customer, package_name)

    if available["available_qty"] >= bottle_quantity :
        wo_doc = frappe.new_doc('Water Order')
        wo_doc.customer = customer
        wo_doc.address = address
        wo_doc.bottle_quantity = bottle_quantity
        wo_doc.delivered_quantity = 0
        wo_doc.outstanding_quantity = bottle_quantity
        wo_doc.consumed_from = package_name
        wo_doc.status = 'Pending'
        wo_doc.delivery_date = delivery_date
        wo_doc.order_date = frappe.utils.today()
        wo_doc.save(ignore_permissions=True)

        total_balance = frappe.db.get_value('Customer Package Purchase', package_name, 'bottles_purchased')
        bottles_ordered = frappe.db.get_value('Customer Package Purchase', package_name, 'bottles_ordered')
        frappe.db.set_value('Customer Package Purchase', package_name, 'bottles_ordered', (bottles_ordered + bottle_quantity) )
        frappe.db.set_value('Customer Package Purchase', package_name, 'bottles_remaining', (total_balance - (bottles_ordered + bottle_quantity)) )

        return {'message':'Water Order placed successfully', 'status':'success'}

    else :
        return {'message':'Available Bottle quantity is less than ordered quantity', 'status':'failed'}







@frappe.whitelist()
def check_available_qty(customer, package_name) :
    available_qty = 0
    water_bottle_product = frappe.db.get_value("Customer Package Purchase",  package_name, "water_bottle_product")
    cust_water_bottle_list = frappe.get_all("Customer Water Bottle", 
                                filters={
                                    "customer" : customer ,
                                    "water_bottle_product" : water_bottle_product ,
                                    "status": 'Active'
                                },
                                fields=["name", "available_quantity"],
                            )
    if cust_water_bottle_list :
        for wat_botle in cust_water_bottle_list :
            available_qty = available_qty + (wat_botle.available_quantity or 0)
    
    return {"available_qty" : available_qty}




# No use
def update_available_qty(customer, package_name, bottle_quantity) :
    available_qty = 0
    water_bottle_product = frappe.db.get_value("Customer Package Purchase",  package_name, "water_bottle_product")
    cust_water_bottle_list = frappe.get_all("Customer Water Bottle", 
                                filters={
                                    "customer" : customer ,
                                    "water_bottle_product" : water_bottle_product ,
                                    "status": 'Active'
                                },
                                fields=["name", "available_quantity"],
                            )
    if cust_water_bottle_list :
        ordered = cust_water_bottle_list[0].ordered_quantity + bottle_quantity
        available = cust_water_bottle_list[0].balance - ordered

        frappe.db.set_value('Customer Water Bottle', cust_water_bottle_list[0].name, 'ordered_quantity', ordered)
        frappe.db.set_value('Customer Water Bottle', cust_water_bottle_list[0].name, 'available_quantity', available)
        

# No use
def get_customer_order_details(customer, package_name) :

    del_qty = 0
    cust_water_order_list = frappe.get_all("Water Order", 
                                filters={
                                    "customer" : customer ,
                                    "consumed_from" : package_name ,
                                    "status": ['IN', ['Partially Delivered', 'Delivered']]
                                },
                                fields=["name", "customer", "consumed_from", "item", "bottle_type", "delivered_quantity", "status"],
                                order_by="delivery_date" 
                            )
    if cust_water_order_list :
        for wo in cust_water_order_list :
            del_qty = del_qty + (wo.delivered_quantity or 0)
    
    return del_qty


# No use
def get_customer_bottle_return_details(customer, package_name) :
    
    bottle_ret_qty = 0
    cust_bottle_ret_list = frappe.get_all("Bottle Return", 
                                filters={
                                    "customer" : customer ,
                                    "customer_package_purchase" : package_name ,
                                    "status": ['IN', ['Partially Delivered', 'Delivered']]
                                },
                                fields=["name", "customer", "customer_package_purchase", "quantity_returned"],
                                order_by="delivery_date" 
                            )
    
    if cust_bottle_ret_list :
        for br in cust_bottle_ret_list :
            bottle_ret_qty = bottle_ret_qty + (br.quantity_returned or 0)
        
    
    return bottle_ret_qty



    







