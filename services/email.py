import os
import logging
from flask import current_app

logger = logging.getLogger(__name__)


def send_auth_email(to_email: str, word1: str, word2: str) -> bool:
    api_key = current_app.config.get("RESEND_API_KEY", "")
    from_addr = current_app.config.get("EMAIL_FROM")

    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;background:#0b0e1a;color:#f0f2fa;padding:40px;border-radius:12px">
      <h2 style="color:#f5a623;margin-bottom:8px">🐯 Carteira Tigrão</h2>
      <p style="color:#8892b0;margin-bottom:32px">Sua senha temporária de acesso:</p>
      <div style="background:#161b2e;border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:24px;text-align:center;margin-bottom:32px">
        <span style="font-size:28px;font-weight:700;letter-spacing:6px;color:#f5a623">
          {word1.upper()} {word2.upper()}
        </span>
      </div>
      <p style="color:#8892b0;font-size:14px">
        Esta senha expira em <strong style="color:#f0f2fa">15 minutos</strong>.<br>
        Se você não solicitou acesso, ignore este e-mail.
      </p>
    </div>
    """

    if not api_key:
        # Modo desenvolvimento: exibe no terminal
        logger.warning("=" * 60)
        logger.warning(f"[DEV] E-mail para: {to_email}")
        logger.warning(f"[DEV] Palavras: {word1.upper()} {word2.upper()}")
        logger.warning("=" * 60)
        print(f"\n>>> SENHA TEMPORÁRIA para {to_email}: {word1.upper()} {word2.upper()}\n")
        return True

    try:
        import resend
        resend.api_key = api_key
        resend.Emails.send({
            "from": from_addr,
            "to": to_email,
            "subject": "Sua senha temporária - Carteira Tigrão",
            "html": html,
        })
        return True
    except Exception as e:
        logger.error(f"Falha ao enviar e-mail: {e}")
        return False
