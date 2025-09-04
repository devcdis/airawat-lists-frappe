import frappe
import random
import string
from frappe import _
from frappe.auth import LoginManager
from frappe.utils import now_datetime, add_to_date
import requests
import re
from frappe.core.doctype.sms_settings.sms_settings import send_sms as send_sms_frappe


OTP_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
OTP_LENGTH = 6
OTP_REGEX = f'^[{re.escape(OTP_CHARS)}]{{{OTP_LENGTH}}}$'

# if nanoid doesn't exist, fallback to random string
try:
    from nanoid import generate
    USE_NANOID = True
except ImportError:
    import random
    import string
    USE_NANOID = False
    frappe.log_error("nanoid not installed, falling back to random generation", "Dependency Warning")

def generate_otp():
    """Generate OTP using nanoid or fallback to random"""
    if USE_NANOID:
        return generate(OTP_CHARS, OTP_LENGTH)
    else:
        return ''.join(random.choices(OTP_CHARS, k=6))


def send_sms(mobile, otp):
    """Send SMS using Frappe's SMS queue"""
    # Check if SMS is enabled
    if not frappe.db.get_single_value('SMS Settings', 'sms_gateway_url'):
        frappe.throw(_("SMS Settings not configured. Please contact administrator."))

    # Create SMS queue document
    message = f"Dear user, your CRS OTP for CRS application is {otp}. Use it to complete authentication. Do not share it. --AIRAWAT RESEARCH FOUNDATION"
    result = send_sms_frappe(receiver_list=[mobile],msg=message)
    return {"success": True}