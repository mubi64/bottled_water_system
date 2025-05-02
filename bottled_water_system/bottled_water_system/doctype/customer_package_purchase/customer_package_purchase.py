# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CustomerPackagePurchase(Document):
	# pass
    def before_save(self) :
        self.bottles_remaining = self.total_bottles - (self.bottles_ordered or 0)
        if self.bottles_remaining == 0 :
            self.status = 'Fully Consumed'
