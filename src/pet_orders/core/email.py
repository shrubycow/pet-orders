from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from pet_orders.settings import settings


async def send_email(email: str, subject: str, body: str) -> None:
    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=body,
        subtype=MessageType.plain,
    )
    fm = FastMail(
        ConnectionConfig(
            MAIL_USERNAME=settings.mail_username,
            MAIL_PASSWORD=settings.mail_password,
            MAIL_FROM=settings.mail_from,
            MAIL_FROM_NAME=settings.mail_from_name,
            MAIL_PORT=settings.mail_port,
            MAIL_SERVER=settings.mail_server,
            MAIL_STARTTLS=settings.mail_starttls,
            MAIL_SSL_TLS=settings.mail_ssl_tls,
            USE_CREDENTIALS=settings.mail_use_credentials,
            VALIDATE_CERTS=settings.mail_validate_certs,
        )
    )
    await fm.send_message(message)
