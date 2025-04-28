# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from bottled_water_system.api.rent_bottles import update_customer_water_bottle_return


class BottleReturn(Document):
	
    def after_insert(self) :

        update_customer_water_bottle_return(self)

        if self.with_security_return == 1 :
            cust_btl_wtr_list = frappe.get_all('Customer Water Bottle',
                                            filters={
                                                'status' : 'Active' ,
                                                'customer' : self.customer ,
                                                'water_bottle_product' : self.water_bottle_product
                                            }
                                )
            if cust_btl_wtr_list :
                cust_btl_wtr_doc = frappe.get_doc('Customer Water Bottle', cust_btl_wtr_list[0].name)
                cust_btl_wtr_doc.append('customer_security_deposit_return',{
                    'bottle_return' : self.name ,
                    'posting_date' : self.return_date ,
                    'payment_entry' : self.payment_entry ,
                    'security_return' : self.security_return ,
                    'quantity' : self.quantity_returned
                })
                cust_btl_wtr_doc.security_deposit_return = (cust_btl_wtr_doc.security_deposit_return or 0) + self.security_return
                cust_btl_wtr_doc.balance_security_deposit = cust_btl_wtr_doc.total_security_deposit - cust_btl_wtr_doc.security_deposit_return
                cust_btl_wtr_doc.returned_quantity = (cust_btl_wtr_doc.returned_quantity or 0) + self.quantity_returned
                cust_btl_wtr_doc.available_quantity = cust_btl_wtr_doc.total_quantity - cust_btl_wtr_doc.returned_quantity
                cust_btl_wtr_doc.save(ignore_permissions=True)





            


    

