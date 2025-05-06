# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from bottled_water_system.api.order import (update_customer_package_purchase, update_customer_water_bottle)
from frappe.utils import flt


class WaterOrder(Document):
            
    def on_trash(self) :
        update_customer_package_purchase(self, False)
        
    
    def after_insert(self) :
        update_customer_water_bottle(self)
        update_customer_package_purchase(self, True)


    def before_save(self) :
        self.outstanding_quantity = flt(self.bottle_quantity) - flt(self.delivered_quantity)

        if self.status != 'Cancelled' :
            if flt(self.delivered_quantity) == flt(0) :
                self.status = 'Pending'
            elif flt(self.delivered_quantity) > flt(0) and flt(self.delivered_quantity) < flt(self.bottle_quantity) :
                self.status = 'Partially Delivered'
            elif flt(self.delivered_quantity) == flt(self.bottle_quantity) :
                self.status = 'Delivered'
    
		
        

		
		


        
        


        

        
