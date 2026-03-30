from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Account, Category

setup_bp = Blueprint("setup", __name__, url_prefix="/setup")

DEFAULT_CATEGORIES = [
    {"name": "Entradas",         "type": "income",     "pct": None, "color": "#22c55e", "order": 0},
    {"name": "Gastos Fixos",     "type": "fixed",      "pct": 30,   "color": "#f5a623", "order": 1},
    {"name": "Gastos Variáveis", "type": "variable",   "pct": 30,   "color": "#3b82f6", "order": 2},
    {"name": "Investimentos",    "type": "investment", "pct": 40,   "color": "#a855f7", "order": 3},
]


@setup_bp.route("/conta", methods=["GET", "POST"])
@login_required
def account():
    if current_user.account:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Informe o nome da conta.", "error")
            return render_template("setup/account.html")

        acct = Account(user_id=current_user.id, name=name)
        db.session.add(acct)
        db.session.flush()  # para obter acct.id

        for c in DEFAULT_CATEGORIES:
            db.session.add(Category(
                account_id=acct.id,
                name=c["name"],
                category_type=c["type"],
                percentage=c["pct"],
                color=c["color"],
                order=c["order"],
            ))

        db.session.commit()
        return redirect(url_for("setup.categories"))

    return render_template("setup/account.html")


@setup_bp.route("/categorias", methods=["GET", "POST"])
@login_required
def categories():
    if not current_user.account:
        return redirect(url_for("setup.account"))

    account = current_user.account
    expense_cats = [c for c in account.categories if c.category_type != "income"]

    if request.method == "POST":
        total = 0
        for cat in expense_cats:
            pct_str = request.form.get(f"pct_{cat.id}", "0")
            try:
                pct = float(pct_str)
            except ValueError:
                pct = 0
            cat.percentage = max(0, min(100, pct))
            total += cat.percentage

        if abs(total - 100) > 0.01:
            flash(f"Os percentuais devem somar 100%. Total atual: {total:.0f}%", "error")
            return render_template("setup/categories.html", categories=expense_cats)

        db.session.commit()
        return redirect(url_for("main.dashboard"))

    return render_template("setup/categories.html", categories=expense_cats)
