import imaplib
import email
from email.header import decode_header
import re
import socket
import os
from flask import Flask, request, render_template_string

app = Flask(__name__)

# --- PREMIUM DASHBOARD WITH IFRAME RENDERER ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FRUX STORE - Full Mail Layout Extractor</title>
    <style>
        body { font-family: sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px; margin: 0; }
        .container { max-width: 900px; margin: 0 auto; background: #1e293b; padding: 25px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        h1 { text-align: center; color: #38bdf8; font-size: 24px; margin-bottom: 25px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; color: #94a3b8; font-weight: bold; }
        input { width: 100%; padding: 12px; border: 1px solid #334155; border-radius: 6px; background: #0f172a; color: #fff; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #0284c7; border: none; border-radius: 6px; color: white; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 10px; }
        button:hover { background: #0369a1; }
        .mail-box { background: #0f172a; border: 1px solid #334155; border-radius: 8px; margin-top: 25px; padding: 15px; }
        .mail-header { font-size: 14px; color: #94a3b8; margin-bottom: 10px; border-bottom: 1px solid #334155; padding-bottom: 8px; line-height: 1.6; }
        .otp-display { background: #e11d48; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 14px; }
        .mail-iframe { width: 100%; height: 600px; border: none; background: white; border-radius: 6px; margin-top: 10px; }
        .status { text-align: center; font-weight: bold; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔥 FRUX STORE - REAL MAIL LAYOUT 🔥</h1>
        <form method="POST" action="/fetch">
            <div class="form-group">
                <label>📧 Gmail Address:</label>
                <input type="text" name="email" placeholder="example@gmail.com" required>
            </div>
            <div class="form-group">
                <label>🔑 16-Digit App Password:</label>
                <input type="password" name="password" placeholder="abcd efgh ijkl mnop" required>
            </div>
            <button type="submit">Fetch Real Full Layout</button>
        </form>

        {% if error %}
            <div class="status" style="color: #f87171;">❌ {{ error }}</div>
        {% endif %}

        {% if mails %}
            <div class="status" style="color: #34d399;">✔ {{ status_msg }}</div>
            {% for mail in mails %}
                <div class="mail-box">
                    <div class="mail-header">
                        <b>📩 From:</b> {{ mail.from_ }}<br>
                        <b>🕒 Date:</b> {{ mail.date_ }}<br>
                        <b>📌 Subject:</b> {{ mail.subject }}<br>
                        <b>🔑 Extracted Code:</b> <span class="otp-display">{{ mail.otp }}</span>
                    </div>
                    <iframe class="mail-iframe" srcdoc="{{ mail.body_html }}"></iframe>
                </div>
            {% endfor %}
        {% endif %}
    </div>
</body>
</html>
"""

def safe_decode(header_value):
    if not header_value: return "None"
    try:
        decoded = decode_header(header_value)
        parts = [text.decode(codec or "utf-8", errors="replace") if isinstance(text, bytes) else str(text) for text, codec in decoded]
        return "".join(parts)
    except: return str(header_value)

def get_html_body(msg):
    """Email ka asli full HTML layout nikalne ke liye"""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        return payload.decode(part.get_content_charset() or "utf-8", errors='replace')
                except: pass
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        plain_text = payload.decode(part.get_content_charset() or "utf-8", errors='replace')
                        return f"<pre style='font-family: sans-serif; padding:15px;'>{plain_text}</pre>"
                except: pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                decoded = payload.decode(msg.get_content_charset() or "utf-8", errors='replace')
                if msg.get_content_type() == "text/html": return decoded
                return f"<pre style='font-family: sans-serif; padding:15px;'>{decoded}</pre>"
        except: pass
    return "<h3>No visual content found in this mail.</h3>"

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/fetch', methods=['POST'])
def fetch_mails():
    username = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()

    socket.setdefaulttimeout(20)
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(username, password)
        mail.select("INBOX", readonly=True)

        _, data = mail.search(None, 'ALL')
        mail_ids = data[0].split()
        
        if not mail_ids:
            mail.logout()
            return render_template_string(HTML_TEMPLATE, error="Inbox khali hai!")

        latest_ids = mail_ids[-3:]
        latest_ids.reverse()

        fetched_mails = []
        for msg_id in latest_ids:
            _, msg_data = mail.fetch(msg_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = safe_decode(msg.get("Subject"))
                    from_ = safe_decode(msg.get("From"))
                    date_ = safe_decode(msg.get("Date"))
                    
                    # Full HTML Layout raw data nikalo
                    body_html = get_html_body(msg)
                    
                    # OTP nikalne ka regex logic
                    clean_text = re.sub(r'<[^>]+>', ' ', body_html)
                    codes = re.findall(r'\b\d{4,8}\b', clean_text)
                    clean_codes = [c for c in codes if c not in ["2024", "2025", "2026", "2027"]]
                    otp = clean_codes[0] if clean_codes else "NOT FOUND"
                    
                    # Quotes ko HTML me escape karein taaki iframe break na ho
                    escaped_html = body_html.replace('"', '&quot;')

                    fetched_mails.append({
                        "subject": subject,
                        "from_": from_,
                        "date_": date_,
                        "body_html": escaped_html,
                        "otp": otp
                    })
        mail.logout()
        return render_template_string(HTML_TEMPLATE, mails=fetched_mails, status_msg="Successfully fetched full mail layouts!")

    except imaplib.IMAP4.error:
        return render_template_string(HTML_TEMPLATE, error="Authentication Failed! App password galat hai.")
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, error=f"Error: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
