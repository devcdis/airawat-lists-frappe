import frappe
import random
import string
from frappe import _
from frappe.auth import LoginManager
from frappe.utils import now_datetime, add_to_date
from frappe.api.utils import send_sms, generate_otp, OTP_REGEX
from werkzeug.routing import Rule
import re

def send_otp():
    """Generate and send OTP to mobile number"""
    data = frappe.form_dict
    mobile = data.get("mobile")
    
    if not mobile or not re.match(r'^\+91[6-9]\d{9}$', mobile):
      return {"success": False, "message": "Invalid mobile number format. Must be +91 followed by 10 digits starting with 6-9"}
    
    # check if user exists with this mobile
    user = frappe.db.get_value("User", {"mobile_no": mobile}, ["name"])
    if not user:
        return {"success": False, "message": "No account found with this mobile number"}
    
    # generate OTP for 5 minutes
    otp = generate_otp()
    frappe.cache().set_value(f"otp:{mobile}", otp, expires_in_sec=300)
    
    # send sms
    try:
        send_sms(mobile, otp)
        return {"success": True, "message": "OTP sent successfully"}
    except Exception as e:
        frappe.log_error(f"Failed to send OTP to {mobile}: {str(e)}", "OTP Error")
        return {"success": False, "message": "Failed to send OTP. Please try again."}

def verify_otp():
    """Verify OTP and login user"""
    data = frappe.form_dict
    mobile = data.get("mobile")
    otp = data.get("otp")
    
    # Validate inputs
    if not mobile or not re.match(r'^\+91[6-9]\d{9}$', mobile) or not otp or not re.match(OTP_REGEX, otp):
        return {"success": False, "message": "Mobile number and OTP are required"}
    
    # Get stored OTP
    stored_otp = frappe.cache().get_value(f"otp:{mobile}")
    if not stored_otp:
        return {"success": False, "message": "Invalid OTP"}
    
    # Verify OTP
    if stored_otp != otp:
        return {"success": False, "message": "Invalid OTP"}
    
    # Get user details
    user = frappe.db.get_value("User", {"mobile_no": mobile}, ["name"])
    if not user:
        return {"success": False, "message": "User not found"}
    
    # Delete OTP from cache
    frappe.cache().delete_value(f"otp:{mobile}")
    
    # Login user
    try:
        login_manager = LoginManager()
        login_manager.login_as(user)
        return {
            "success": True, 
            "message": "Login successful",
            "user": user,
        }
    except Exception as e:
        frappe.log_error(f"Login failed for {mobile}: {str(e)}", "Login Error")
        return {"success": False, "message": "Login failed. Please try again."}

# URL rules
url_rules = [
    # User Accounts level APIs
    Rule("/accounts/send-otp", methods=["POST"], endpoint=send_otp),
    Rule("/accounts/verify-otp", methods=["POST"], endpoint=verify_otp),
]
