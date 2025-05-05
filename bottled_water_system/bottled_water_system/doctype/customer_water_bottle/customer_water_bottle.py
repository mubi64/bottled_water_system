# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CustomerWaterBottle(Document):
	# pass
    def before_save(self) :
        self.balance_security_deposit = (self.total_security_deposit or 0) - (self.security_deposit_return or 0)
        self.total_available_bottles = (self.available_quantity or 0)

        del_qty = 0
        ret_qty = 0

        if self.bottle_product_ledger :
            for row in self.bottle_product_ledger :
                del_qty = del_qty + (row.delivered_quantity or 0)
                ret_qty = ret_qty + (row.return_quantity or 0)

        self.customer_hand = del_qty - ret_qty
        self.company_hand = self.total_available_bottles - self.customer_hand





