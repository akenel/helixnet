# File: src/services/camper_email_service.py
"""
Camper & Tour Email Notification Service.
Uses SMTP to MailHog (dev) or real SMTP (production).

Templates in Italian for Sicilian customers.
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)

# MailHog in Docker compose
SMTP_HOST = "mailhog"
SMTP_PORT = 1025
FROM_EMAIL = "noreply@camperandtour.it"
FROM_NAME = "Camper & Tour - Trapani"


def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send HTML email via SMTP"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())

        logger.info(f"Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Email send failed to {to_email}: {e}")
        return False


def _email_wrapper(content: str) -> str:
    """Wrap content in branded email template"""
    return f"""
    <html>
    <body style="font-family: 'Helvetica Neue', Arial, sans-serif; margin: 0; padding: 0; background: #f5f5f5;">
        <div style="max-width: 600px; margin: 20px auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <div style="background: linear-gradient(135deg, #d97706, #b45309); padding: 24px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Camper &amp; Tour</h1>
                <p style="color: #fef3c7; margin: 4px 0 0; font-size: 14px;">Gestione Servizi - Trapani</p>
            </div>
            <div style="padding: 24px;">
                {content}
            </div>
            <div style="background: #f9fafb; padding: 16px 24px; text-align: center; font-size: 12px; color: #9ca3af;">
                Camper &amp; Tour sas - Via F. Culcasi, 4 - 91100 Trapani<br>
                Tel: +39 0923 534452 | info@camperandtour.it
            </div>
        </div>
    </body>
    </html>
    """


def send_quotation_email(to_email: str, customer_name: str, quote_number: str, total: str, deposit: str) -> bool:
    """Quotation sent to customer"""
    content = f"""
    <h2 style="color: #1f2937;">Gentile {customer_name},</h2>
    <p>Le inviamo il preventivo <strong>{quote_number}</strong> per il servizio richiesto.</p>
    <div style="background: #fffbeb; border-left: 4px solid #d97706; padding: 16px; margin: 16px 0; border-radius: 4px;">
        <p style="margin: 0;"><strong>Totale preventivo:</strong> {total}</p>
        <p style="margin: 8px 0 0;"><strong>Acconto richiesto (25%):</strong> {deposit}</p>
    </div>
    <p>Il preventivo include IVA al 22%. Per accettare, contatti la nostra officina.</p>
    <p style="color: #6b7280; font-size: 14px;">Cordiali saluti,<br>Il team Camper &amp; Tour</p>
    """
    return _send_email(to_email, f"Preventivo {quote_number} - Camper & Tour", _email_wrapper(content))


def send_quotation_accepted_email(to_email: str, customer_name: str, quote_number: str) -> bool:
    """Confirmation that quotation was accepted"""
    content = f"""
    <h2 style="color: #1f2937;">Gentile {customer_name},</h2>
    <p>Il suo preventivo <strong>{quote_number}</strong> e stato accettato.</p>
    <p>Procederemo con i lavori non appena ricevuto l'acconto.</p>
    <p style="color: #6b7280; font-size: 14px;">Cordiali saluti,<br>Il team Camper &amp; Tour</p>
    """
    return _send_email(to_email, f"Preventivo {quote_number} Accettato - Camper & Tour", _email_wrapper(content))


def send_deposit_received_email(to_email: str, customer_name: str, amount: str, job_number: str) -> bool:
    """Deposit payment received"""
    content = f"""
    <h2 style="color: #1f2937;">Gentile {customer_name},</h2>
    <p>Confermiamo la ricezione dell'acconto di <strong>{amount}</strong> per il lavoro <strong>{job_number}</strong>.</p>
    <div style="background: #ecfdf5; border-left: 4px solid #10b981; padding: 16px; margin: 16px 0; border-radius: 4px;">
        <p style="margin: 0;">I lavori sul suo veicolo inizieranno a breve.</p>
    </div>
    <p style="color: #6b7280; font-size: 14px;">Cordiali saluti,<br>Il team Camper &amp; Tour</p>
    """
    return _send_email(to_email, f"Acconto Ricevuto - Lavoro {job_number}", _email_wrapper(content))


def send_job_complete_email(to_email: str, customer_name: str, job_number: str, vehicle_plate: str) -> bool:
    """Job completed notification"""
    content = f"""
    <h2 style="color: #1f2937;">Gentile {customer_name},</h2>
    <p>Il lavoro <strong>{job_number}</strong> sul veicolo <strong>{vehicle_plate}</strong> e stato completato!</p>
    <div style="background: #ecfdf5; border-left: 4px solid #10b981; padding: 16px; margin: 16px 0; border-radius: 4px;">
        <p style="margin: 0; font-size: 18px;">Il suo veicolo e pronto per il ritiro.</p>
    </div>
    <p>La preghiamo di contattarci per concordare il ritiro.</p>
    <p><strong>Tel:</strong> +39 0923 534452</p>
    <p style="color: #6b7280; font-size: 14px;">Cordiali saluti,<br>Il team Camper &amp; Tour</p>
    """
    return _send_email(to_email, f"Veicolo Pronto - {vehicle_plate}", _email_wrapper(content))


def send_invoice_email(to_email: str, customer_name: str, invoice_number: str, total: str, amount_due: str) -> bool:
    """Invoice sent to customer"""
    content = f"""
    <h2 style="color: #1f2937;">Gentile {customer_name},</h2>
    <p>Le inviamo la fattura <strong>{invoice_number}</strong>.</p>
    <div style="background: #eff6ff; border-left: 4px solid #3b82f6; padding: 16px; margin: 16px 0; border-radius: 4px;">
        <p style="margin: 0;"><strong>Totale fattura:</strong> {total}</p>
        <p style="margin: 8px 0 0;"><strong>Importo dovuto:</strong> {amount_due}</p>
        <p style="margin: 8px 0 0; font-size: 12px; color: #6b7280;">IVA 22% inclusa</p>
    </div>
    <p style="color: #6b7280; font-size: 14px;">Cordiali saluti,<br>Il team Camper &amp; Tour</p>
    """
    return _send_email(to_email, f"Fattura {invoice_number} - Camper & Tour", _email_wrapper(content))
