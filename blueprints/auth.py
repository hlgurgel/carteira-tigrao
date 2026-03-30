from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required
from extensions import db
from models import User, AuthToken
from services.bip39 import generate_auth_words
from services.email import send_auth_email

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if not email or "@" not in email:
            flash("Informe um e-mail válido.", "error")
            return render_template("auth/login.html")

        word1, word2 = generate_auth_words()
        expiry = datetime.utcnow() + timedelta(
            minutes=current_app.config["AUTH_TOKEN_EXPIRY_MINUTES"]
        )
        token = AuthToken(email=email, word1=word1, word2=word2, expires_at=expiry)
        db.session.add(token)
        db.session.commit()

        if not send_auth_email(email, word1, word2):
            flash("Erro ao enviar e-mail. Tente novamente.", "error")
            return render_template("auth/login.html")

        session["pending_email"] = email
        return redirect(url_for("auth.verify"))

    return render_template("auth/login.html")


@auth_bp.route("/verify", methods=["GET", "POST"])
def verify():
    email = session.get("pending_email")
    if not email:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        w1 = request.form.get("word1", "").strip().lower()
        w2 = request.form.get("word2", "").strip().lower()

        token = (
            AuthToken.query
            .filter_by(email=email, used=False)
            .order_by(AuthToken.created_at.desc())
            .first()
        )

        if not token or token.is_expired:
            flash("Senha expirada. Solicite uma nova.", "error")
            session.pop("pending_email", None)
            return redirect(url_for("auth.login"))

        if token.word1 != w1 or token.word2 != w2:
            flash("Palavras incorretas. Tente novamente.", "error")
            return render_template("auth/verify.html", email=email)

        token.used = True
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email)
            db.session.add(user)

        db.session.commit()
        session.pop("pending_email", None)
        login_user(user, remember=True)

        if not user.account:
            return redirect(url_for("setup.account"))
        return redirect(url_for("main.dashboard"))

    return render_template("auth/verify.html", email=email)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
