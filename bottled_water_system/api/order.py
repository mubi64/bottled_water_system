
import frappe

from bottled_water_system.api.common import get_customer
from frappe.utils import flt


@frappe.whitelist()
def place_water_order(package_name , bottle_quantity, delivery_date, address) :


    customer = get_customer()

    if delivery_date < frappe.utils.today() :
        return {'message':'Delivery Date must be in future dates', 'status':'failed'}
    
    remaining_balance = frappe.db.get_value('Customer Package Purchase', package_name, 'bottles_remaining')

    if flt(remaining_balance) < flt(bottle_quantity) :
        return {'message':'Your remaining balance from package purchase is less than ordered quantity', 'status':'failed'}


    available = check_available_qty(customer, package_name)

    if flt(available["available_qty"]) >= flt(bottle_quantity) :
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
        wo_doc.insert(ignore_permissions=True)

        return {'message':'Water Order placed successfully.', 'status':'success'}

    else :
        bottle_package = frappe.db.get_value("Customer Package Purchase",  package_name, "bottle_package")
        return {'message': f'Available water bottle product "{bottle_package}" is {available["available_qty"]}.', 'status':'failed'}



@frappe.whitelist()
def get_customer_water_order() :
    customer = get_customer()
    water_order_list = frappe.get_all('Water Order',
                                    filters = {
                                        'customer' : customer ,
                                        'status' : ['!=', 'Cancelled']
                                    },
                                    fields = ['*']
                                )
    return water_order_list



@frappe.whitelist()
def update_customer_package_purchase(self, bool) :
    bottles_purchased = frappe.db.get_value('Customer Package Purchase', self.consumed_from, 'bottles_purchased')
    prev_bottles_order = frappe.db.get_value('Customer Package Purchase', self.consumed_from, 'bottles_ordered')
    
    if bool == True :
        bottles_order = flt(prev_bottles_order or 0) + flt(self.bottle_quantity or 0)
    else :
        bottles_order = flt(prev_bottles_order or 0) - flt(self.bottle_quantity or 0)

    remaining_bottles = bottles_purchased - bottles_order
    
    frappe.db.set_value('Customer Package Purchase', self.consumed_from, 'bottles_ordered', bottles_order)
    frappe.db.set_value('Customer Package Purchase', self.consumed_from, 'bottles_remaining', remaining_bottles)




@frappe.whitelist()
def update_customer_water_bottle(self) :
    bottle_package = frappe.db.get_value('Customer Package Purchase', self.consumed_from, 'bottle_package')
    water_bottle_product = frappe.db.get_value('Bottle Package', bottle_package, 'water_bottle_product')
    cust_water_botl_list = frappe.get_list('Customer Water Bottle',
                                            filters = {
                                                'customer' : self.customer ,
                                                'water_bottle_product' : water_bottle_product ,
                                                'status' : 'Active'
                                            },ignore_permissions=True
                                        )
    
    if cust_water_botl_list :
        cust_water_botl_doc = frappe.get_doc('Customer Water Bottle', cust_water_botl_list[0].name)
        cust_water_botl_doc.flags.ignore_permissions = True
        cust_water_botl_doc.append('bottle_product_ledger',{
            'water_order' : self.name ,
            'ordered_quantity' : self.bottle_quantity ,
            'delivered_quantity' : self.delivered_quantity ,
            'outstanding_quantity' : self.outstanding_quantity ,
        })
        cust_water_botl_doc.save()



@frappe.whitelist()
def check_available_qty(customer, package_name) :
    available_qty = 0
    bottle_package = frappe.db.get_value("Customer Package Purchase",  package_name, "bottle_package")
    water_bottle_product = frappe.db.get_value("Bottle Package",  bottle_package, "water_bottle_product")
    
    cust_water_bottle_list = frappe.get_all("Customer Water Bottle", 
                                filters={
                                    "customer" : customer ,
                                    "water_bottle_product" : water_bottle_product ,
                                    "status": 'Active'
                                },
                                fields=["name", "available_quantity"],
                                ignore_permissions=True
                            )
    if cust_water_bottle_list :
        for wat_botle in cust_water_bottle_list :
            available_qty = available_qty + (wat_botle.available_quantity or 0)
    
    return {"available_qty" : available_qty}




@frappe.whitelist()
def water_order_delivery(water_order, delivered_quantity) :

    prev_delivered_quantity = frappe.db.get_value('Water Order', water_order, 'delivered_quantity')
    prev_outstanding_qty = frappe.db.get_value('Water Order', water_order, 'outstanding_quantity')
    if flt(prev_outstanding_qty) < flt(delivered_quantity) :
        return {'message':'Delivered quantity can not be greater than outstanding quantity' , 'status':'failed'}

    else :
        frappe.db.set_value('Water Order', water_order, 'delivered_quantity', prev_delivered_quantity + delivered_quantity)
        frappe.db.set_value('Water Order', water_order, 'outstanding_quantity', prev_outstanding_qty - delivered_quantity)
        water_order_doc = frappe.get_doc('Water Order', water_order)
        set_water_order_status(water_order_doc)
        update_bottle_ledger_on_delivery(water_order_doc)

        return {'message':'Water Order Updated' , 'status':'success'}


@frappe.whitelist()
def update_bottle_ledger_on_delivery(water_order_doc) :
    water_bottle_product = frappe.db.get_value('Customer Package Purchase', water_order_doc.consumed_from, 'water_bottle_product')
    cust_water_botl_list = frappe.get_list('Customer Water Bottle',
                                           filters={
                                               'customer' : water_order_doc.customer ,
                                               'water_bottle_product' : water_bottle_product ,
                                               'status' : 'Active'
                                           }
                                           ,ignore_permissions=True
                                        )
    # print(cust_water_botl_list)
    if cust_water_botl_list :
        cust_water_botl_doc = frappe.get_doc('Customer Water Bottle', cust_water_botl_list[0].name)
        if cust_water_botl_doc.bottle_product_ledger :
            for row in cust_water_botl_doc.bottle_product_ledger :
                if row.bottle_transaction_type == 'Depart' and row.water_order == water_order_doc.name :
                    row.delivered_quantity = water_order_doc.delivered_quantity
                    row.outstanding_quantity = water_order_doc.outstanding_quantity
                    break
            cust_water_botl_doc.save(ignore_permissions=True)
    




@frappe.whitelist()
def set_water_order_status(self) :
    if self.status != 'Cancelled' :
        if flt(self.delivered_quantity) == flt(0) :
            self.status = 'Pending'
        elif flt(self.delivered_quantity) > flt(0) and flt(self.delivered_quantity) < flt(self.bottle_quantity) :
            self.status = 'Partially Delivered'
        elif flt(self.delivered_quantity) == flt(self.bottle_quantity) :
            self.status = 'Delivered'
        self.save(ignore_permissions=True)



    



