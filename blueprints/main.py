from datetime import date, datetime
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import extract, func
from extensions import db
from models import Account, Category, Tag, Transaction

main_bp = Blueprint("main", __name__)


def _q_sum(account_id, cat_id, tx_type, year, month=None):
    q = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.account_id == account_id,
        Transaction.category_id == cat_id,
        Transaction.transaction_type == tx_type,
        extract("year", Transaction.date) == year,
    )
    if month:
        q = q.filter(extract("month", Transaction.date) == month)
    result = q.scalar()
    return Decimal(str(result)) if result else Decimal("0")


def _get_summary(account, year, month=None):
    cats = account.categories
    income_cat = next((c for c in cats if c.category_type == "income"), None)

    # Entradas gerais (distribuídas pelos percentuais)
    general_income = (
        _q_sum(account.id, income_cat.id, "income", year, month)
        if income_cat else Decimal("0")
    )

    summary = []
    for cat in cats:
        if cat.category_type == "income":
            summary.append({
                "cat": cat,
                "income": general_income,
                "allocated": None,
                "spent": None,
                "available": None,
                "pct_used": None,
            })
        else:
            # Entrada direta para esta categoria (ex: dividendos → Investimentos)
            direct = _q_sum(account.id, cat.id, "income", year, month)
            pct = Decimal(str(cat.percentage)) if cat.percentage else Decimal("0")
            allocated = (general_income * pct / 100 + direct).quantize(Decimal("0.01"))
            spent = _q_sum(account.id, cat.id, "expense", year, month)
            available = allocated - spent
            pct_used = float(spent / allocated * 100) if allocated else 0
            summary.append({
                "cat": cat,
                "income": None,
                "allocated": allocated,
                "spent": spent,
                "available": available,
                "pct_used": round(pct_used, 1),
            })

    return general_income, summary


@main_bp.route("/dashboard")
@login_required
def dashboard():
    if not current_user.account:
        return redirect(url_for("setup.account"))

    account = current_user.account
    today = date.today()

    view = request.args.get("view", "month")
    year = int(request.args.get("year", today.year))
    month = int(request.args.get("month", today.month)) if view == "month" else None

    total_income, summary = _get_summary(account, year, month)

    q = Transaction.query.filter(
        Transaction.account_id == account.id,
        extract("year", Transaction.date) == year,
    )
    if month:
        q = q.filter(extract("month", Transaction.date) == month)
    transactions = q.order_by(Transaction.date.desc(), Transaction.id.desc()).all()

    if view == "month":
        prev = {"year": year - 1, "month": 12, "view": "month"} if month == 1 else {"year": year, "month": month - 1, "view": "month"}
        nxt  = {"year": year + 1, "month": 1,  "view": "month"} if month == 12 else {"year": year, "month": month + 1, "view": "month"}
    else:
        prev = {"year": year - 1, "view": "year"}
        nxt  = {"year": year + 1, "view": "year"}

    month_names = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    period_label = f"{month_names[month - 1]} {year}" if view == "month" else str(year)

    monthly_data = []
    if view == "year":
        for m in range(1, 13):
            inc, _ = _get_summary(account, year, m)
            monthly_data.append({"month": month_names[m - 1], "income": float(inc)})

    expense_cats = [item["cat"] for item in summary if item["cat"].category_type != "income"]

    return render_template(
        "main/dashboard.html",
        account=account,
        summary=summary,
        expense_cats=expense_cats,
        total_income=total_income,
        transactions=transactions,
        view=view,
        year=year,
        month=month,
        prev=prev,
        nxt=nxt,
        period_label=period_label,
        monthly_data=monthly_data,
        today=today,
    )


@main_bp.route("/transacao/adicionar", methods=["POST"])
@login_required
def add_transaction():
    account = current_user.account
    if not account:
        return redirect(url_for("setup.account"))

    amount_str = request.form.get("amount", "").replace(",", ".").strip()
    tag_name   = request.form.get("tag", "").strip()
    cat_id     = request.form.get("category_id", "").strip()
    date_str   = request.form.get("date", "").strip()
    tx_type    = request.form.get("tx_type", "expense").strip()

    errors = []
    if not amount_str:  errors.append("Informe o valor.")
    if not tag_name:    errors.append("Informe a tag.")
    if not cat_id:      errors.append("Selecione a categoria.")

    try:
        amount = Decimal(amount_str)
        if amount <= 0:
            errors.append("O valor deve ser positivo.")
    except Exception:
        errors.append("Valor inválido.")

    if errors:
        for e in errors:
            flash(e, "error")
        return redirect(url_for("main.dashboard"))

    cat = Category.query.filter_by(id=int(cat_id), account_id=account.id).first()
    if not cat:
        flash("Categoria inválida.", "error")
        return redirect(url_for("main.dashboard"))

    # Se a categoria é "income" e o tx_type veio como expense, corrige
    if cat.category_type == "income":
        tx_type = "income"

    tag = Tag.query.filter(
        Tag.account_id == account.id,
        func.lower(Tag.name) == tag_name.lower()
    ).first()
    if not tag:
        tag = Tag(account_id=account.id, name=tag_name)
        db.session.add(tag)
        db.session.flush()

    try:
        tx_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()
    except ValueError:
        tx_date = date.today()

    tx = Transaction(
        account_id=account.id,
        category_id=cat.id,
        tag_id=tag.id,
        amount=amount,
        transaction_type=tx_type,
        date=tx_date,
    )
    db.session.add(tx)
    db.session.commit()

    return redirect(url_for("main.dashboard", view="month", year=tx_date.year, month=tx_date.month))


@main_bp.route("/transacao/<int:tx_id>/apagar", methods=["POST"])
@login_required
def delete_transaction(tx_id):
    tx = Transaction.query.filter_by(
        id=tx_id, account_id=current_user.account.id
    ).first_or_404()
    db.session.delete(tx)
    db.session.commit()
    return jsonify({"ok": True})


@main_bp.route("/conta/apagar", methods=["POST"])
@login_required
def delete_account():
    user = current_user
    account = user.account
    if account:
        Transaction.query.filter_by(account_id=account.id).delete()
        Tag.query.filter_by(account_id=account.id).delete()
        Category.query.filter_by(account_id=account.id).delete()
        db.session.delete(account)
    from models import AuthToken
    AuthToken.query.filter_by(email=user.email).delete()
    db.session.delete(user)
    db.session.commit()
    from flask_login import logout_user
    logout_user()
    flash("Conta apagada com sucesso.", "info")
    return redirect(url_for("auth.login"))


@main_bp.route("/api/tags")
@login_required
def api_tags():
    q = request.args.get("q", "").strip()
    account = current_user.account
    if not account or not q:
        return jsonify([])
    tags = Tag.query.filter(
        Tag.account_id == account.id,
        Tag.name.ilike(f"%{q}%")
    ).order_by(Tag.name).limit(10).all()
    return jsonify([t.name for t in tags])
