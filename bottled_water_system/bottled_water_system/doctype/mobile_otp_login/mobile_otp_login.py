# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

from bottled_water_system.api.account import (send_otp)


class MobileOTPLogin(Document):
	pass
    # def before_save(self) :
    #     # number = '+923092288164'
    #     number = '+923079921460'
    #     message = "Ye aagya range me"
    #     send_otp(number)
        

    
