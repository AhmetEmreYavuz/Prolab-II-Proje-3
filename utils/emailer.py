# utils/emailer.py
import os, smtplib, ssl
import configparser
from email.message import EmailMessage

# Yapılandırma dosyasından SMTP ayarlarını yükle
config = configparser.ConfigParser()
config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.ini')

# Varsayılan ayarlar
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = ""
SMTP_PASS = ""
SENDER = ""
USE_SMTP = False

# Eğer yapılandırma dosyası varsa, ayarları yükle
if os.path.exists(config_file):
    config.read(config_file)
    if 'Email' in config:
        SMTP_HOST = config['Email'].get('SMTP_HOST', SMTP_HOST)
        SMTP_PORT = config['Email'].getint('SMTP_PORT', SMTP_PORT)
        SMTP_USER = config['Email'].get('SMTP_USER', SMTP_USER)
        SMTP_PASS = config['Email'].get('SMTP_PASS', SMTP_PASS)
        SENDER = config['Email'].get('SMTP_SENDER', SMTP_USER)
        USE_SMTP = config['Email'].getboolean('USE_SMTP', False)


def save_smtp_settings(host, port, user, password, sender, use_smtp=True):
    """SMTP ayarlarını config.ini dosyasına kaydeder."""
    if not config.has_section('Email'):
        config.add_section('Email')

    config['Email']['SMTP_HOST'] = host
    config['Email']['SMTP_PORT'] = str(port)
    config['Email']['SMTP_USER'] = user
    config['Email']['SMTP_PASS'] = password
    config['Email']['SMTP_SENDER'] = sender or user
    config['Email']['USE_SMTP'] = 'yes' if use_smtp else 'no'

    with open(config_file, 'w') as f:
        config.write(f)

    # Global değişkenleri güncelle
    global SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SENDER, USE_SMTP
    SMTP_HOST = host
    SMTP_PORT = int(port)
    SMTP_USER = user
    SMTP_PASS = password
    SENDER = sender or user
    USE_SMTP = use_smtp


def send_mail(to_addr: str, subject: str, body: str):
    """E-posta gönderir. Ayarlar yapılandırılmamışsa terminalde gösterir."""
    if not USE_SMTP or not all([SMTP_HOST, SMTP_USER, SMTP_PASS]):
        print(f"(MockMail) To: {to_addr}\nSubj: {subject}\n{body}\n")
        return

    msg = EmailMessage()
    msg["From"] = SENDER
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        if SMTP_PORT == 465:  # SSL port
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as server:
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
        else:  # TLS port (587) veya diğer
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
        return True
    except Exception as e:
        print(f"E-posta gönderilirken hata oluştu: {str(e)}")
        return False