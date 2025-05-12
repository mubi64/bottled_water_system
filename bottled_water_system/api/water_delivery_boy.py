


import frappe
from bottled_water_system.api.common import get_customer





@frappe.whitelist()
def get_water_orders_for_delivery_boy() :
    current_user = frappe.session.user
    water_order_list = frappe.get_all('Water Order',
                            filters = {
                                        'assigned_to' : current_user
                                      },
                            fields = ['customer', 'bottle_quantity', 'delivered_quantity', 'outstanding_quantity', 'item', 'bottle_type', 'status', 'order_date', 'delivery_date', 'address']   
                        )
    if water_order_list :
        for row in water_order_list :
            add_doc = frappe.get_doc('Address', row.address)
            row['latitude'] = add_doc.custom_latitude
            row['longitude'] = add_doc.custom_longitude

    return water_order_list



@frappe.whitelist()
def get_bottle_return_for_delivery_boy() :
    current_user = frappe.session.user
    bottle_retun_list = frappe.get_all('Bottle Return', 
                                filters = {
                                            'owner' : current_user
                                          },
                                fields = ['customer', 'water_bottle_product', 'item', 'bottle_type', 'return_date', 'quantity_returned', 'with_security_return', 'payment_entry']
                        )
    if bottle_retun_list :
        for row in bottle_retun_list :
            if row.payment_entry :
                payment_entry_doc = frappe.get_doc('Bottle Return', row.payment_entry)
                row['status'] = payment_entry_doc.status
                row['amount'] = payment_entry_doc.paid_amount
                row['currency'] = payment_entry_doc.paid_from_account_currency

    return bottle_retun_list




