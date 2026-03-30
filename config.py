import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

    _db_url = os.environ.get("DATABASE_URL", "sqlite:///carteira.db")
    # Render usa "postgres://" mas SQLAlchemy exige "postgresql://"
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Sessão permanente até o usuário fazer logout
    REMEMBER_COOKIE_DURATION = timedelta(days=3650)
    REMEMBER_COOKIE_HTTPONLY = True

    # Resend (e-mail)
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
    EMAIL_FROM = os.environ.get(
        "EMAIL_FROM", "Carteira Tigrão <onboarding@resend.dev>"
    )

    # Token de autenticação expira em 15 minutos
    AUTH_TOKEN_EXPIRY_MINUTES = 15
