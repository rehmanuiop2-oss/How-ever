import imaplib
import email
from email.header import decode_header
import re
import socket
import os
from flask import Flask, request, render_template_string

app = Flask(__name__)

# --- UPDATED PROFESSIONAL UI FOR PROPER LAYOUT RENDERING ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FRUX STORE - Premium Mail Viewer</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            background-color: #0b0f19; 
            color: #f1f5f9; 
            padding: 15px; 
            margin: 0; 
        }
        .container { 
            max-width: 650px; 
            margin: 0 auto; 
            background: #151f32; 
            padding: 20px; 
            border-radius: 12px; 
            box-shadow: 0 10px 25px rgba(0,0,0,0.4); 
        }
        h1 { 
            text-align: center; 
            color: #38bdf8; 
            font-size: 22px; 
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .form-group { 
            margin-bottom: 15px; 
        }
        label { 
            display: block; 
            margin-bottom: 6px; 
            color: #94a3b8; 
            font-size: 13px;
            font-weight: 600; 
        }
        input { 
            width: 100%; 
            padding: 12px; 
            border: 1px solid #24334d; 
            border-radius: 8px; 
            background: #0b0f19; 
            color: #fff; 
            box-sizing: border-box; 
            font-size: 14px;
        }
        input:focus {
            border-color: #38bdf8;
            outline: none;
        }
        button { 
            width: 100%; 
            padding: 14px; 
            background: #0284c7; 
            border: none; 
            border-radius: 8px; 
            color: white; 
            font-size: 15px; 
            font-weight: bold; 
            cursor: pointer; 
            margin-top: 5px; 
            transition: background 0.2s;
        }
        button:hover { 
            background: #0369a1; 
        }
        .mail-box { 
            background: #111827; 
            border: 1px solid #1f2937; 
            border-radius: 10px; 
            margin-top: 20px; 
            padding: 15px; 
            overflow: hidden;
        }
        .mail-header { 
            font-size: 13px; 
            color: #9ca3af; 
            margin-bottom: 12px; 
            border-bottom: 1px solid #1f2937; 
            padding-bottom: 10px; 
            line-height: 1.5; 
        }
        .otp-container {
            margin-top: 8px;
            background: rgba(225, 29, 72, 0.1);
            border: 1px solid #e11d48;
            padding: 8px;
            border-radius: 6px;
            display: inline-block;
        }
        .otp-display { 
            color: #f43f5e; 
            font-weight: bold; 
            font-size: 16px; 
        }
        /* Adjusted container for handling structured email layout display */
        .mail-display-wrapper {
            width: 100%;
            background: #ffffff;
            border-radius: 6px;
            margin-top: 10px;
            overflow: hidden;
        }
        .mail-iframe { 
            width: 100%; 
            height: 500px; 
            border: none; 
            display: block;
        }
        .status { 
            text-align: center; 
            font-weight: bold; 
            margin-top: 15px; 
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔥 FRUX PREMIUM VIEWER 🔥</h1>
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
                        <div class="otp-container">
                            <b>🔑 Extracted Code:</b> <span class="otp-display">{{ mail.otp }}</span>
                        </div>
                    </div>
                    <div class="mail-display-wrapper">
                        <iframe class="mail-iframe" srcdoc="{{ mail.body_html }}"></iframe>
                    </div>
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
                        return f"<pre style='font-family:sans-serif; padding:15px; color:#333;'>{plain_text}</pre>"
                except: pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                decoded = payload.decode(msg.get_content_charset() or "utf-8", errors='replace')
                if msg.get_content_type() == "text/html": return decoded
                return f"<pre style='font-family:sans-serif; padding:15px; color:#333;'>{decoded}</pre>"
        except: pass
    return "<p style='padding:15px; color:#333;'>No body content available.</p>"

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
            return render_template_string(HTML_TEMPLATE, error="Inbox is empty.")

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
                    
                    body_html = get_html_body(msg)
                    
                    clean_text = re.sub(r'<[^>]+>', ' ', body_html)
                    codes = re.findall(r'\b\d{4,8}\b', clean_text)
                    clean_codes = [c for c in codes if c not in ["2024", "2025", "2026", "2027"]]
                    otp = clean_codes[0] if clean_codes else "NOT FOUND"
                    
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
        return render_template_string(HTML_TEMPLATE, error="Authentication Failed!")
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, error=f"Error: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
