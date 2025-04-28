
import frappe

from bottled_water_system.api.common import get_customer


@frappe.whitelist(allow_guest=True)
def rent_water_bottle_product(water_bottle_product, quantity):

    customer = get_customer()

    security_deposit_string = get_security_deposit(water_bottle_product, quantity)

    mode_of_payment = frappe.db.get_single_value('Bottled Water Settings', 'mode_of_payment')
    mode_of_payment_doc = frappe.get_doc('Mode of Payment', mode_of_payment)

    acc_paid_to = None
    if mode_of_payment_doc.accounts :
        for x in mode_of_payment_doc.accounts :
            if x.default_account :
                acc_paid_to = x.default_account
                break
        
        if not acc_paid_to :
            return {'message':'Account None does not match with Company in Mode of Account:', 'status':'failed'}

    else :
        return {'message':'Please set default Cash or Bank account in Mode of Payment', 'status':'failed'}


    cust_water_bottle_list = frappe.get_all("Customer Water Bottle", 
        filters={
            "customer": customer,
            "water_bottle_product": water_bottle_product,
            "status": 'Active'
        },
        fields=["name"],
    )


    payment_type = 'Receive'
    paid_amount = security_deposit_string['total_security_deposit']
    received_amount = security_deposit_string['total_security_deposit']
    reference_no = 'Rent Bottle Water'
    pay_ent_doc = create_payment_entry(payment_type, mode_of_payment, customer, paid_amount, received_amount, reference_no, acc_paid_to )




    if cust_water_bottle_list:
        cust_water_bottle_doc = frappe.get_doc('Customer Water Bottle', cust_water_bottle_list[0].name)
        cust_water_bottle_doc.flags.ignore_permissions = True
        cust_water_bottle_doc.append('customer_security_deposit', {
            'posting_date': frappe.utils.today(),
            'security_deposit': security_deposit_string['total_security_deposit'],
            'quantity': quantity,
            'payment_entry': pay_ent_doc.name,
        })
        cust_water_bottle_doc.total_quantity += quantity
        cust_water_bottle_doc.available_quantity = cust_water_bottle_doc.total_quantity - (cust_water_bottle_doc.returned_quantity or 0)
        cust_water_bottle_doc.total_security_deposit += security_deposit_string['total_security_deposit']
        cust_water_bottle_doc.balance_security_deposit = cust_water_bottle_doc.total_security_deposit - cust_water_bottle_doc.security_deposit_return
        cust_water_bottle_doc.save()

        return {'message': 'Customer Water Bottle updated', 'status':'success'}

    else:
        cust_water_bottle_doc = frappe.new_doc('Customer Water Bottle')
        cust_water_bottle_doc.customer = customer
        cust_water_bottle_doc.water_bottle_product = water_bottle_product
        cust_water_bottle_doc.total_quantity = quantity
        cust_water_bottle_doc.returned_quantity = 0
        cust_water_bottle_doc.available_quantity = quantity
        cust_water_bottle_doc.total_security_deposit = security_deposit_string['total_security_deposit']
        cust_water_bottle_doc.status = 'Active'
        cust_water_bottle_doc.append('customer_security_deposit', {
            'posting_date': frappe.utils.today(),
            'security_deposit': security_deposit_string['total_security_deposit'],
            'quantity': quantity,
            'payment_entry': pay_ent_doc.name,
        })
        cust_water_bottle_doc.insert(ignore_permissions=True)

        return {'message': 'New Customer Water Bottle created', 'status':'success'}
     






@frappe.whitelist()
def get_security_deposit(water_bottle_product, quantity) :
    
    wat_bot_pd_price = frappe.db.get_value('Water Bottle Product', water_bottle_product, 'price')
    total_wat_bot_pd_price = (wat_bot_pd_price or 0) * quantity
    return {'total_security_deposit': total_wat_bot_pd_price}




@frappe.whitelist()
def bottle_return(water_order, bottle_returns) :

    customer = get_customer()

    if bottle_returns :
        for row in bottle_returns :
            botl_ret_doc = frappe.new_doc('Bottle Return')
            botl_ret_doc.customer = customer
            botl_ret_doc.water_bottle_product = row["water_bottle_product"]
            botl_ret_doc.quantity_returned = row["quantity"]
            botl_ret_doc.return_date = frappe.utils.today()
            botl_ret_doc.water_order = water_order
            botl_ret_doc.insert(ignore_permissions=True)
        
        return {'message':"Bottle Returns Created", 'status':'success'}

    else :
        return {'message':"No Bottle Returns Found", 'status':'failed'}





@frappe.whitelist()
def update_customer_water_bottle_return(self) :
    
    water_bottle_product = self.water_bottle_product
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
            'bottle_transaction_type' : 'Return' ,
            'bottle_return' : self.name ,
            'return_quantity' : self.quantity_returned ,
        })
        cust_water_botl_doc.save()



@frappe.whitelist()
def security_return(water_bottle_product, quantity) :
    current_user = frappe.session.user
    customer_list = frappe.db.sql("""
        SELECT parent 
        FROM `tabPortal User` 
        WHERE user = %s
        LIMIT 1
    """, (current_user,), as_dict=True)
    if not customer_list:
        frappe.throw("No customer found for the current user.")
    customer = customer_list[0].parent

    botl_ret_doc = frappe.new_doc('Bottle Return')
    botl_ret_doc.customer = customer
    botl_ret_doc.water_bottle_product = water_bottle_product
    botl_ret_doc.quantity_returned = quantity
    botl_ret_doc.return_date = frappe.utils.today()

    payment_type = 'Pay'
    mode_of_payment = frappe.db.get_single_value('Bottled Water Settings', 'mode_of_payment')
    security_deposit_string = get_security_deposit(water_bottle_product, quantity)
    paid_amount = security_deposit_string['total_security_deposit']
    received_amount = security_deposit_string['total_security_deposit']
    reference_no = 'Bottle Return'
    acc_paid_to = None

    mode_of_payment_doc = frappe.get_doc('Mode of Payment', mode_of_payment)
    if mode_of_payment_doc.accounts :
        for x in mode_of_payment_doc.accounts :
            if x.default_account :
                acc_paid_to = x.default_account
                break
        
        if not acc_paid_to :
            return {'message':'Account None does not match with Company in Mode of Account:', 'status':'failed'}
    else :
        return {'message':'Please set default Cash or Bank account in Mode of Payment', 'status':'failed'}

    pay_ent_doc = create_payment_entry(payment_type, mode_of_payment, customer, paid_amount, received_amount, reference_no, acc_paid_to )
    botl_ret_doc.payment_entry = pay_ent_doc.name
    botl_ret_doc.with_security_return = 1
    botl_ret_doc.security_return = pay_ent_doc.paid_amount

    botl_ret_doc.insert(ignore_permissions=True)

    return { 'message':'bottle returned and payment entry created', 'payment_entry': pay_ent_doc.name, 'status':'success'}

    
    






def create_payment_entry(payment_type, mode_of_payment, customer, paid_amount, received_amount, reference_no, acc_paid_to ) :

    current_user = frappe.session.user
    frappe.set_user("Administrator")

    pay_ent_doc = frappe.new_doc('Payment Entry')
    pay_ent_doc.payment_type = payment_type
    pay_ent_doc.posting_date = frappe.utils.today()
    pay_ent_doc.mode_of_payment = mode_of_payment
    pay_ent_doc.party_type = 'Customer'
    pay_ent_doc.party = customer
    pay_ent_doc.paid_amount = paid_amount
    pay_ent_doc.received_amount = received_amount
    pay_ent_doc.reference_date = frappe.utils.today()
    pay_ent_doc.reference_no = reference_no
    pay_ent_doc.target_exchange_rate = 1
    if payment_type == 'Receive' :
        pay_ent_doc.paid_to = acc_paid_to
    elif payment_type == 'Pay' :
        pay_ent_doc.paid_from = acc_paid_to
    pay_ent_doc.insert(ignore_permissions=True)
    pay_ent_doc.submit()

    # Switch back to original user
    frappe.set_user(current_user)

    return pay_ent_doc






