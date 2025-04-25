import random
import frappe

from frappe.utils import now_datetime, add_to_date


@frappe.whitelist(allow_guest=True)
def send_otp(mobile_number):
    # return 1
    otp = str(random.randint(100000, 999999))
    expiry = add_to_date(now_datetime(), minutes=5)

    # Replace with your SMS API call here
    # ret = send_sms(mobile_number, f"Your OTP is {otp}")

    # if ret :
    doc = frappe.get_doc({
        "doctype": "Mobile OTP Login",
        "mobile_number": mobile_number,
        "otp": otp,
        "is_verified": 0,
        "otp_expiry": expiry
    })
    doc.insert(ignore_permissions=True)
    return {"status": "success", "message": "OTP sent"}
    # else :
        # return {"status": "failed", "message": "OTP not sent"}


# def send_sms(number, message):
#     # Example for UltraMsg or any other service
#     # Replace this with real API call





@frappe.whitelist(allow_guest=True)
def verify_otp(mobile_number, input_otp):
    from frappe.utils import now_datetime

    result = frappe.get_all("Mobile OTP Login",
        filters={
            "mobile_number": mobile_number,
            "otp": input_otp,
            "is_verified": 0
        },
        order_by="creation desc",
        limit=1
    )

    if not result:
        return {"status": "error", "message": "Invalid or expired OTP"}

    doc = frappe.get_doc("Mobile OTP Login", result[0].name)
    if now_datetime() > doc.otp_expiry:
        return {"status": "error", "message": "OTP expired"}

    doc.is_verified = 1
    doc.save(ignore_permissions=True)

    user = frappe.db.get_value("User", {"username": mobile_number}, "name")
    if user:
        # Auto login old user
        frappe.local.login_manager.user = user
        frappe.local.login_manager.post_login()

        return {
            "status": "success",
            "message": "OTP verified. User logged in.",
            "sid": frappe.session.sid,
            "is_new_user": False
        }

    # Don't create user yet — wait for frontend to send data
    return {
        "status": "success",
        "message": "OTP verified. New user.",
        "is_new_user": True
    }


@frappe.whitelist(allow_guest=True)
def complete_registration_and_login(mobile_number, full_name, email, birth_date, gender):
    # Make sure OTP was verified
    otp_verified = frappe.db.exists("Mobile OTP Login", {
        "mobile_number": mobile_number,
        "is_verified": 1
    })

    if not otp_verified:
        return {"status": "error", "message": "OTP not verified"}

    # Check again if user already exists
    if frappe.db.exists("User", {"username": mobile_number}):
        return {"status": "error", "message": "User already exists"}

    
    try:
        # Split full name into first, middle, last
        name_parts = full_name.strip().split()
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        middle_name = " ".join(name_parts[1:-1]) if len(name_parts) > 2 else ""
        last_name = name_parts[-1] if len(name_parts) > 1 else ""

        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "username": mobile_number,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "birth_date": birth_date,
            "gender": gender,
            "mobile_no": mobile_number,
            "enabled": 1,
            "send_welcome_email": 0,
            "roles": [
                {
                    "role": "Customer"
                }
            ]
        }).insert(ignore_permissions=True)

        # Create Customer linked to this User
        customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": full_name,
            "customer_type": "Individual",
            "gender": gender,
            "portal_users": [
                {
                    "user": user.name
                }
            ]
        }).insert(ignore_permissions=True)

        # Try to find existing contact by email or mobile number
        existing_contact = frappe.db.get_all(
            "Contact",
            filters={
                "email_id": email,
                "mobile_no": mobile_number
            },
            fields=["name"]
        )

        if existing_contact:
            # Link the customer if not already linked
            contact = frappe.get_doc("Contact", existing_contact[0].name)
            already_linked = any(link.link_doctype == "Customer" and link.link_name == customer.name for link in contact.links)
            if not already_linked:
                contact.is_primary_contact = 1
                contact.is_billing_contact = 1
                contact.append("links", {
                    "link_doctype": "Customer",
                    "link_name": customer.name
                })
                contact.save(ignore_permissions=True)
        else:
            # Create Contact for Customer
            frappe.get_doc({
                "doctype": "Contact",
                "first_name": first_name,
                "middle_name": middle_name,
                "last_name": last_name,
                "phone": mobile_number,
                "is_primary_contact": 1,
                "is_billing_contact": 1,
                "email_ids": [
                    {
                        "email_id": email,
                        "is_primary": 1
                    }
                ],
                "phone_nos": [
                    {
                        "phone": mobile_number,
                        "is_primary_mobile_no": 1
                    }
                ],
                "links": [
                    {
                        "link_doctype": "Customer",
                        "link_name": customer.name
                    }
                ]
            }).insert(ignore_permissions=True)
        
        settings = frappe.get_single("Bottled Water Settings")

        if settings.award_bottle_to_new_users and settings.award_bottle_quantity > 0:
            frappe.get_doc({
                "doctype": "Customer Water Bottle",
                "customer": customer.name,
                "water_bottle_product": settings.award_bottle_product,
                "quantity": settings.award_bottle_quantity,
                "available_quantity": settings.award_bottle_quantity,
                "security_deposit": 0,
                "status": "Active"
            }).insert(ignore_permissions=True)


        frappe.local.login_manager.user = user.name
        frappe.local.login_manager.post_login()

        return {
            "status": "success",
            "message": "User created and logged in",
            "sid": frappe.session.sid
        }

    except Exception as e:
        return {"status": "error", "message": f"Registration failed: {frappe.get_traceback()}"}


