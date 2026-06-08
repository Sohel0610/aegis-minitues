import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os

logger = logging.getLogger(__name__)

# ======== CONFIGURE YOUR EMAIL SETTINGS HERE ========
SMTP_SERVER = "smtp.adani.com"
SMTP_PORT = 25
SMTP_USER = "no-reply-ai-agel@adani.com"
# SMTP_PASS = "" # Not provided, assuming no password needed for port 25 or handled by server whitelist
# Admin Emails - Access requests will be sent to all addresses in this list
ADMIN_EMAILS = [
    "Abhishek.MahadevMane@adani.com", 
    # Add extra admin emails here (e.g., "admin2@adani.com")
]
BASE_URL = "https://aegis.adani.com"

def send_email(subject, body, to_email=None, to_emails=None, is_html=True):
    """
    Sends an email using the configured SMTP settings.
    Handles both to_email (string) or to_emails (list/string).
    """
    # Normalize recipients
    recipients = to_emails if to_emails else to_email
    if isinstance(recipients, list):
        recipients = ", ".join(recipients)
    
    if not recipients:
        logger.error("send_email called without any recipients")
        return False

    logger.info(f"📧 [EMAIL SERVICE] Starting email process to: {recipients}")
    logger.info(f"📧 [EMAIL SERVICE] Subject: {subject}")

    try:
        msg = MIMEMultipart()
        msg['From'] = f"Aegis Platform <{SMTP_USER}>"
        msg['To'] = recipients
        msg['Subject'] = subject

        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))

        logger.info(f"📧 [EMAIL SERVICE] Connecting to SMTP Server: {SMTP_SERVER}:{SMTP_PORT}...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            # server.set_debuglevel(1) # Enable for extremely detailed SMTP logs
            
            logger.info("📧 [EMAIL SERVICE] Connection established. Sending message...")
            server.send_message(msg)
            
        logger.info(f"✅ [EMAIL SERVICE] SUCCESS: Email sent to {recipients}")
        return True
    except smtplib.SMTPConnectError:
        logger.error(f"❌ [EMAIL SERVICE] CONNECTION ERROR: Could not connect to {SMTP_SERVER}")
        return False
    except smtplib.SMTPAuthenticationError:
        logger.error(f"❌ [EMAIL SERVICE] AUTH ERROR: SMTP credentials rejected")
        return False
    except Exception as e:
        logger.error(f"❌ [EMAIL SERVICE] UNEXPECTED ERROR: {str(e)}")
        return False

def format_request_id(request_id):
    """Format numeric ID into professional #AGS-YYYY-XXXX format."""
    try:
        year = datetime.datetime.now().year
        return f"#AGS-{year}-{int(request_id):04d}"
    except:
        return f"#AGS-{request_id}"

def get_current_timestamp():
    """Get current timestamp in professional format."""
    return datetime.datetime.now().strftime("%b %d, %Y at %I:%M %p") + " IST"

def format_application_name(route_path):
    """Clean route path into a friendly application name."""
    if not route_path:
        return ".aegis"
    # Remove leading slash
    name = route_path.lstrip('/')
    # Replace dashes and underscores with spaces
    name = name.replace('-', ' ').replace('_', ' ')
    # Capitalize each word
    return name.title()

def get_admin_request_template(request_id, requester_name, requester_email, requested_route, justification, access_level="Read & Analyze", target_admin_email=None):
    """
    Exact HTML template provided by user for admin access request notifications.
    """
    formatted_id = format_request_id(request_id)
    timestamp = get_current_timestamp()
    app_name = format_application_name(requested_route)
    
    # Use the specific admin email for the approval links if provided
    admin_ref = target_admin_email if target_admin_email else (ADMIN_EMAILS[0] if ADMIN_EMAILS else "")
    
    approve_link = f"{BASE_URL}/api/access-requests/email-action?id={request_id}&action=approve&email={admin_ref}"
    reject_link = f"{BASE_URL}/api/access-requests/email-action?id={request_id}&action=reject&email={admin_ref}"
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Access Request - {app_name}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: 'Segoe UI', Arial, sans-serif;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; padding: 40px 0;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="700" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                    <!-- Accent Bar -->
                    <tr><td height="5" style="background: #FBB040;"></td></tr>
                    <!-- Header -->
                    <tr>
                        <td align="center" style="background-color: #005696; padding: 25px 30px;">
                            <h1 style="color: #ffffff; font-size: 28px; font-weight: 800; margin: 0; letter-spacing: 2px;">AEGIS</h1>
                            <p style="color: rgba(255,255,255,0.9); font-size: 13px; margin: 5px 0 0; text-transform: uppercase; letter-spacing: 1px;">Access Management System</p>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 30px 50px 20px;">
                            <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td>
                                        <p style="font-size: 12px; color: #005696; font-family: monospace; margin: 0;">Request ID: {formatted_id}</p>
                                    </td>
                                    <td align="right">
                                        <p style="font-size: 11px; color: #64748b; margin: 0;">{timestamp}</p>
                                    </td>
                                </tr>
                            </table>
                            <h2 style="font-size: 20px; color: #1e293b; margin: 20px 0 10px;">Hello Administrator,</h2>
                            <p style="font-size: 15px; color: #475569; line-height: 1.6; margin-bottom: 20px;">
                                A new access request has been received for <strong>{app_name}</strong>.
                            </p>
                            <!-- Info Box -->
                            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e2e8f0; border-radius: 10px; border-left: 6px solid #FBB040; background-color: #f8fafc;">
                                <tr>
                                    <td style="padding: 20px 25px;">
                                        <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                            <tr>
                                                <td width="50%" style="padding-bottom: 15px;">
                                                    <span style="font-size: 10px; color: #64748b; text-transform: uppercase; font-weight: 700; display: block; margin-bottom: 3px;">Requester Name</span>
                                                    <span style="font-size: 15px; color: #1e293b; font-weight: 700;">{requester_name}</span>
                                                </td>
                                                <td width="50%" style="padding-bottom: 15px;">
                                                    <span style="font-size: 10px; color: #64748b; text-transform: uppercase; font-weight: 700; display: block; margin-bottom: 3px;">Email Address</span>
                                                    <span style="font-size: 15px; color: #1e293b;">{requester_email}</span>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td width="50%" style="padding-bottom: 15px;">
                                                    <span style="font-size: 10px; color: #64748b; text-transform: uppercase; font-weight: 700; display: block; margin-bottom: 3px;">Application</span>
                                                    <span style="font-size: 15px; color: #005696; font-weight: 700;">{app_name}</span>
                                                </td>
                                                <td width="50%" style="padding-bottom: 15px;">
                                                    <span style="font-size: 10px; color: #64748b; text-transform: uppercase; font-weight: 700; display: block; margin-bottom: 3px;">Access Level</span>
                                                    <span style="font-size: 12px; background-color: #005696; color: #ffffff; padding: 4px 10px; border-radius: 12px; font-weight: 700;">{access_level}</span>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td colspan="2">
                                                    <span style="font-size: 10px; color: #64748b; text-transform: uppercase; font-weight: 700; display: block; margin-bottom: 3px;">Justification</span>
                                                    <div style="background-color: #fefce8; border-left: 4px solid #FBB040; padding: 12px; border-radius: 6px;">
                                                        <p style="font-size: 14px; font-style: italic; color: #475569; margin: 0; line-height: 1.4;">"{justification}"</p>
                                                    </div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            <!-- Actions -->
                            <p style="text-align: center; font-size: 17px; font-weight: 700; color: #1e293b; margin: 30px 0 20px;">Review and take action</p>
                            <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <table border="0" cellpadding="0" cellspacing="15">
                                            <tr>
                                                <td style="background-color: #10b981; border-radius: 8px;">
                                                    <a href="{approve_link}" style="display: inline-block; padding: 14px 30px; color: #ffffff; text-decoration: none; font-size: 14px; font-weight: 700;">✓ Grant Access</a>
                                                </td>
                                                <td style="background-color: #ef4444; border-radius: 8px;">
                                                    <a href="{reject_link}" style="display: inline-block; padding: 14px 30px; color: #ffffff; text-decoration: none; font-size: 14px; font-weight: 700;">✕ Decline Request</a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 30px 50px;">
                            <div style="border-left: 4px solid #005696; padding-left: 20px; margin-bottom: 20px;">
                                <p style="font-size: 14px; color: #64748b; margin: 0 0 3px;">Warm regards,</p>
                                <p style="font-size: 16px; color: #005696; font-weight: 700; margin: 0 0 3px;">Renewables AI Team</p>
                                <p style="font-size: 13px; color: #475569; margin: 0;">Internal Helpdesk: <strong>57769</strong></p>
                            </div>
                            <p style="font-size: 11px; text-align: center; color: #94a3b8; margin: 0; line-height: 1.5;">
                                Automated security message from AEGIS. Do not share.<br>
                                <strong style="color: #005696; font-style: italic; font-size: 13px;">Growth with Goodness</strong>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

def get_user_confirmation_template(requester_name, requested_route, status, request_id=None, access_level="Read & Analyze"):
    """
    Exact HTML template provided by user for user approval/rejection notifications.
    """
    formatted_id = format_request_id(request_id) if request_id else "#AGS-2026-N/A"
    timestamp = get_current_timestamp()
    app_name = format_application_name(requested_route)
    
    if status == "approved":
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Access Approved - {app_name}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: 'Segoe UI', Arial, sans-serif;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; padding: 40px 0;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="700" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 10px rgba(16, 185, 129, 0.1);">
                    <!-- Accent Bar -->
                    <tr><td height="5" style="background: #10b981;"></td></tr>
                    <!-- Header -->
                    <tr>
                        <td align="center" style="background-color: #005696; padding: 25px 30px;">
                            <h1 style="color: #ffffff; font-size: 28px; font-weight: 800; margin: 0; letter-spacing: 2px;">AEGIS</h1>
                            <p style="color: rgba(255,255,255,0.9); font-size: 13px; margin: 5px 0 0; text-transform: uppercase;">Access Granted</p>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 30px 50px 20px;">
                            <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td>
                                        <p style="font-size: 12px; color: #005696; font-family: monospace; margin: 0;">Request ID: {formatted_id}</p>
                                    </td>
                                    <td align="right">
                                        <p style="font-size: 11px; color: #64748b; margin: 0;">{timestamp}</p>
                                    </td>
                                </tr>
                            </table>
                            <h2 style="font-size: 20px; color: #1e293b; margin: 20px 0 10px;">Hello {requester_name},</h2>
                            <div style="text-align: center; margin: 20px 0;">
                                <div style="display: inline-block; background-color: #10b981; color: #ffffff; padding: 10px 22px; border-radius: 25px; font-size: 14px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">✓ Request Approved</div>
                            </div>
                            <div style="background-color: #ecfdf5; border-left: 6px solid #10b981; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
                                <p style="font-size: 16px; color: #064e3b; margin: 0; line-height: 1.5;">
                                    Your request for access to <strong>{app_name}</strong> has been <strong>approved</strong>.
                                </p>
                            </div>
                            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden;">
                                <tr>
                                    <td width="33%" style="padding: 20px; background-color: #f8fafc; border-right: 1px solid #e2e8f0;">
                                        <span style="font-size: 10px; color: #64748b; text-transform: uppercase; font-weight: 700; display: block; margin-bottom: 3px;">Application</span>
                                        <div style="font-size: 15px; color: #1e293b; font-weight: 700;">{app_name}</div>
                                    </td>
                                    <td width="33%" style="padding: 20px; background-color: #ffffff; border-right: 1px solid #e2e8f0;">
                                        <span style="font-size: 10px; color: #64748b; text-transform: uppercase; font-weight: 700; display: block; margin-bottom: 3px;">Access Level</span>
                                        <div style="font-size: 12px; background-color: #005696; color: #ffffff; padding: 4px 10px; border-radius: 12px; font-weight: 700; display: inline-block;">{access_level}</div>
                                    </td>
                                    <td width="33%" style="padding: 20px; background-color: #f8fafc;">
                                        <span style="font-size: 10px; color: #64748b; text-transform: uppercase; font-weight: 700; display: block; margin-bottom: 3px;">Status</span>
                                        <div style="font-size: 15px; color: #10b981; font-weight: 700;">Active</div>
                                    </td>
                                </tr>
                            </table>
                            <!-- Primary CTA -->
                            <div style="text-align: center; margin-top: 30px;">
                                <table border="0" cellpadding="0" cellspacing="0" align="center">
                                    <tr>
                                        <td style="background-color: #005696; border-radius: 8px;">
                                            <a href="{BASE_URL}" style="display: inline-block; padding: 14px 35px; color: #ffffff; text-decoration: none; font-size: 15px; font-weight: 700;">🚀 Sign in to AEGIS</a>
                                        </td>
                                    </tr>
                                </table>
                            </div>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 30px 50px;">
                            <div style="border-left: 4px solid #005696; padding-left: 20px; margin-bottom: 20px;">
                                <p style="font-size: 14px; color: #64748b; margin: 0 0 3px;">Warm regards,</p>
                                <p style="font-size: 16px; color: #005696; font-weight: 700; margin: 0 0 3px;">Renewables AI Team</p>
                                <p style="font-size: 13px; color: #475569; margin: 0;">Helpdesk: <strong>57769</strong></p>
                            </div>
                            <p style="font-size: 11px; text-align: center; color: #94a3b8; margin: 0; line-height: 1.5;">
                                Automated message from AEGIS. Keep for your records.<br>
                                <strong style="color: #005696; font-style: italic; font-size: 13px;">Growth with Goodness</strong>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
    elif status == "pending":
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Access Request Received - {app_name}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: 'Segoe UI', Arial, sans-serif;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; padding: 40px 0;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="700" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 10px rgba(251, 176, 64, 0.1);">
                    <!-- Accent Bar -->
                    <tr><td height="5" style="background: #FBB040;"></td></tr>
                    <!-- Header -->
                    <tr>
                        <td align="center" style="background-color: #005696; padding: 25px 30px;">
                            <h1 style="color: #ffffff; font-size: 28px; font-weight: 800; margin: 0; letter-spacing: 2px;">AEGIS</h1>
                            <p style="color: rgba(255,255,255,0.9); font-size: 13px; margin: 5px 0 0; text-transform: uppercase;">Request Received</p>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 30px 50px 20px;">
                            <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td>
                                        <p style="font-size: 12px; color: #005696; font-family: monospace; margin: 0;">Request ID: {formatted_id}</p>
                                    </td>
                                    <td align="right">
                                        <p style="font-size: 11px; color: #64748b; margin: 0;">{timestamp}</p>
                                    </td>
                                </tr>
                            </table>
                            <h2 style="font-size: 20px; color: #1e293b; margin: 20px 0 10px;">Hello {requester_name},</h2>
                            <div style="text-align: center; margin: 20px 0;">
                                <div style="display: inline-block; background-color: #FBB040; color: #ffffff; padding: 10px 22px; border-radius: 25px; font-size: 14px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">⏳ Pending Review</div>
                            </div>
                            <div style="background-color: #fffde7; border-left: 6px solid #FBB040; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
                                <p style="font-size: 16px; color: #713f12; margin: 0; line-height: 1.5;">
                                    Your request for access to <strong>{app_name}</strong> has been received and is currently <strong>pending review</strong>.
                                </p>
                            </div>
                            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden;">
                                <tr>
                                    <td width="50%" style="padding: 20px; background-color: #f8fafc; border-right: 1px solid #e2e8f0;">
                                        <span style="font-size: 10px; color: #64748b; text-transform: uppercase; font-weight: 700; display: block; margin-bottom: 3px;">Application</span>
                                        <div style="font-size: 15px; color: #1e293b; font-weight: 700;">{app_name}</div>
                                    </td>
                                    <td width="50%" style="padding: 20px; background-color: #ffffff;">
                                        <span style="font-size: 10px; color: #64748b; text-transform: uppercase; font-weight: 700; display: block; margin-bottom: 3px;">Status</span>
                                        <div style="font-size: 15px; color: #d97706; font-weight: 700;">Pending Review</div>
                                    </td>
                                </tr>
                            </table>
                            <p style="font-size: 14px; color: #475569; line-height: 1.6; margin-top: 25px;">
                                You will receive another email notification as soon as the administrator reviews and takes action on your request.
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 30px 50px;">
                            <div style="border-left: 4px solid #005696; padding-left: 20px; margin-bottom: 20px;">
                                <p style="font-size: 14px; color: #64748b; margin: 0 0 3px;">Warm regards,</p>
                                <p style="font-size: 16px; color: #005696; font-weight: 700; margin: 0 0 3px;">Renewables AI Team</p>
                                <p style="font-size: 13px; color: #475569; margin: 0;">Helpdesk: <strong>57769</strong></p>
                            </div>
                            <p style="font-size: 11px; text-align: center; color: #94a3b8; margin: 0; line-height: 1.5;">
                                Automated message from AEGIS. Keep for your records.<br>
                                <strong style="color: #005696; font-style: italic; font-size: 13px;">Growth with Goodness</strong>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
    else:
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Access Request Update - {app_name}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: 'Segoe UI', Arial, sans-serif;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; padding: 40px 0;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="700" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                    <!-- Accent Bar -->
                    <tr><td height="5" style="background: #ef4444;"></td></tr>
                    <!-- Header -->
                    <tr>
                        <td align="center" style="background-color: #005696; padding: 25px 30px;">
                            <h1 style="color: #ffffff; font-size: 28px; font-weight: 800; margin: 0; letter-spacing: 2px;">AEGIS</h1>
                            <p style="color: rgba(255,255,255,0.9); font-size: 13px; margin: 5px 0 0; text-transform: uppercase;">Request Update</p>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 30px 50px 20px;">
                            <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td>
                                        <p style="font-size: 12px; color: #005696; font-family: monospace; margin: 0;">Request ID: {formatted_id}</p>
                                    </td>
                                    <td align="right">
                                        <p style="font-size: 11px; color: #64748b; margin: 0;">{timestamp}</p>
                                    </td>
                                </tr>
                            </table>
                            <h2 style="font-size: 20px; color: #1e293b; margin: 20px 0 10px;">Hello {requester_name},</h2>
                            <div style="text-align: center; margin: 20px 0;">
                                <div style="display: inline-block; background-color: #ef4444; color: #ffffff; padding: 10px 22px; border-radius: 25px; font-size: 14px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">✕ Request Declined</div>
                            </div>
                            <div style="background-color: #fef2f2; border-left: 6px solid #ef4444; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
                                <p style="font-size: 16px; color: #991b1b; margin: 0; line-height: 1.5;">
                                    Your request for access to <strong>{app_name}</strong> has been <strong>declined</strong>.
                                </p>
                            </div>
                            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden;">
                                <tr>
                                    <td style="padding: 20px; background-color: #f8fafc;">
                                        <span style="font-size: 10px; color: #64748b; text-transform: uppercase; font-weight: 700; display: block; margin-bottom: 3px;">Application</span>
                                        <div style="font-size: 15px; color: #1e293b; font-weight: 700;">{app_name}</div>
                                    </td>
                                </tr>
                            </table>
                            <p style="font-size: 14px; color: #475569; line-height: 1.6; margin-top: 25px;">
                                If you believe this is a mistake, please reach out to the AEGIS administrator.
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 30px 50px;">
                            <div style="border-left: 4px solid #005696; padding-left: 20px; margin-bottom: 20px;">
                                <p style="font-size: 14px; color: #64748b; margin: 0 0 3px;">Warm regards,</p>
                                <p style="font-size: 16px; color: #005696; font-weight: 700; margin: 0 0 3px;">Renewables AI Team</p>
                                <p style="font-size: 13px; color: #475569; margin: 0;">Helpdesk: <strong>57769</strong></p>
                            </div>
                            <p style="font-size: 11px; text-align: center; color: #94a3b8; margin: 0; line-height: 1.5;">
                                Automated message from AEGIS. Keep for your records.<br>
                                <strong style="color: #005696; font-style: italic; font-size: 13px;">Growth with Goodness</strong>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
