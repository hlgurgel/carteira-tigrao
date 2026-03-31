from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Account, Category

setup_bp = Blueprint("setup", __name__, url_prefix="/setup")

DEFAULT_CATEGORIES = [
    {"name": "Entradas",         "type": "income",     "pct": None, "color": "#22c55e", "order": 0},
    {"name": "Gastos Fixos",     "type": "expense",    "pct": 30,   "color": "#f5a623", "order": 1},
    {"name": "Gastos Variáveis", "type": "expense",    "pct": 30,   "color": "#3b82f6", "order": 2},
    {"name": "Investimentos",    "type": "expense",    "pct": 40,   "color": "#a855f7", "order": 3},
]

PRESET_COLORS = [
    "#f5a623", "#3b82f6", "#a855f7", "#22c55e",
    "#ef4444", "#ec4899", "#eab308", "#06b6d4",
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
        db.session.flush()

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
        ids     = request.form.getlist("cat_ids[]")
        names   = request.form.getlist("cat_names[]")
        pcts    = request.form.getlist("cat_pcts[]")
        colors  = request.form.getlist("cat_colors[]")
        deletes = set(request.form.getlist("cat_delete[]"))

        # Valida
        if not any(n.strip() for n, i in zip(names, ids) if i not in deletes):
            flash("É necessário ter ao menos uma categoria de gastos.", "error")
            return render_template("setup/categories.html",
                                   categories=expense_cats, preset_colors=PRESET_COLORS)

        total = 0
        for i, pct_str in enumerate(pcts):
            if ids[i] in deletes:
                continue
            try:
                total += float(pct_str)
            except ValueError:
                pass

        if abs(total - 100) > 0.01:
            flash(f"Os percentuais devem somar 100%. Total atual: {total:.0f}%", "error")
            return render_template("setup/categories.html",
                                   categories=expense_cats, preset_colors=PRESET_COLORS)

        # Apaga as marcadas (sem transações)
        for del_id in deletes:
            if del_id == "new":
                continue
            cat = Category.query.filter_by(id=int(del_id), account_id=account.id).first()
            if cat:
                from models import Transaction
                has_tx = Transaction.query.filter_by(category_id=cat.id).first()
                if has_tx:
                    flash(f'Categoria "{cat.name}" tem movimentações e não pode ser removida.', "error")
                    continue
                db.session.delete(cat)

        # Atualiza as existentes e cria as novas
        for idx, cat_id in enumerate(ids):
            if cat_id in deletes:
                continue
            name  = names[idx].strip()
            color = colors[idx] if colors[idx] in PRESET_COLORS else PRESET_COLORS[0]
            try:
                pct = max(0, min(100, float(pcts[idx])))
            except ValueError:
                pct = 0

            if not name:
                continue

            if cat_id == "new":
                db.session.add(Category(
                    account_id=account.id,
                    name=name,
                    category_type="expense",
                    percentage=pct,
                    color=color,
                    order=100 + idx,
                ))
            else:
                cat = Category.query.filter_by(id=int(cat_id), account_id=account.id).first()
                if cat:
                    cat.name       = name
                    cat.color      = color
                    cat.percentage = pct

        db.session.commit()
        return redirect(url_for("main.dashboard"))

    return render_template("setup/categories.html",
                           categories=expense_cats, preset_colors=PRESET_COLORS)
