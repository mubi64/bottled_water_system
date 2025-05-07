

import frappe
import stripe
from bottled_water_system.api.common import get_customer
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry # type: ignore

stripe.api_key = frappe.db.get_single_value('Bottled Water Settings','secret_key')



@frappe.whitelist()
def make_payment(card_number, exp_month, exp_year, cvc, is_bottle_rent, sales_invoice, customer_water_bottle) :

    
    amount = 0
    if is_bottle_rent != 1 :
        currency = frappe.db.get_value('Sales Invoice', sales_invoice, 'currency')
        amount = frappe.db.get_value('Sales Invoice', sales_invoice, 'grand_total')
    else :
        company = frappe.defaults.get_user_default("company")
        if not company:
            frappe.throw("No default company set for the current user.")
        company_currency = frappe.db.get_value("Company", company, "default_currency") or "PKR"

        if customer_water_bottle :
            for row in customer_water_bottle :
                price = 0
                sub_amount = 0
                price = frappe.db.get_value('Water Bottle Product', row['water_bottle_product'], 'price')
                sub_amount = (price or 0) * row['quantity']
                amount = amount + sub_amount
                currency = company_currency

    amount = int(amount * 100)
    token = create_card_token(card_number, exp_month, exp_year, cvc)
    payment_method_id = create_payment_method(token)
    payment_intent_id = make_payment_intent(payment_method_id, amount, currency)
    payment_confirm = confirm_payment_intent(payment_intent_id, payment_method_id)
    
    if is_bottle_rent != 1 :
        submit_sales_invoice(sales_invoice)
    
        current_user = frappe.session.user
        frappe.set_user('Administrator')

        pe = get_payment_entry('Sales Invoice', sales_invoice)
        pe.reference_no = 'Card'
        pe.docstatus = 1
        
        frappe.set_user(current_user)
        
        pe.insert(ignore_permissions=True)

        return payment_confirm
    else :
        return payment_confirm


def submit_sales_invoice(sales_invoice) :
    si_doc = frappe.get_doc('Sales Invoice', sales_invoice)
    if si_doc.docstatus == 0 :
        si_doc.docstatus = 1
        si_doc.save(ignore_permissions=True)
        frappe.db.commit()


def create_card_token(card_number, exp_month, exp_year, cvc) :

    token  = stripe.Token.create(
      card={
        "number": card_number,
        "exp_month": exp_month,
        "exp_year": exp_year,
        "cvc": cvc,
      },
    )

    return token.id




def create_payment_method(token) :
    customer = get_customer()
    payment_method = stripe.PaymentMethod.create(
        type="card",
        card={
            "token": token
        },
        billing_details={
            "name": customer,
            "email": frappe.session.user
        }
    )

    return payment_method.id





def make_payment_intent(payment_method_id, amount, currency) :

    payment_intent = stripe.PaymentIntent.create(
      amount=amount,
      currency=currency,
      payment_method= payment_method_id,
      automatic_payment_methods={"enabled": True},
    )

    # print(payment_intent.id)
    return payment_intent.id




def confirm_payment_intent(payment_intent_id, payment_method_id) :

    payment_intent = stripe.PaymentIntent.confirm(
    payment_intent_id,
    payment_method=payment_method_id,
    return_url="https://www.example.com",

    )

    return payment_intent











