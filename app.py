from flask import Flask, render_template, redirect, url_for
from flask_login import current_user
from config import Config
from extensions import db, login_manager, migrate


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Faça login para continuar."
    login_manager.login_message_category = "info"

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from blueprints.auth import auth_bp
    from blueprints.setup import setup_bp
    from blueprints.main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(setup_bp)
    app.register_blueprint(main_bp)

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("main.dashboard"))
        return render_template("index.html")

    with app.app_context():
        db.create_all()
        _auto_migrate(app)

    return app


def _auto_migrate(app):
    """Aplica migrações de coluna sem precisar de comando manual."""
    from sqlalchemy import inspect, text
    insp = inspect(db.engine)
    if "transactions" not in insp.get_table_names():
        return
    cols = [c["name"] for c in insp.get_columns("transactions")]
    if "transaction_type" not in cols:
        with db.engine.begin() as conn:
            conn.execute(text(
                "ALTER TABLE transactions ADD COLUMN transaction_type VARCHAR(10) NOT NULL DEFAULT 'expense'"
            ))
            conn.execute(text(
                "UPDATE transactions SET transaction_type = "
                "CASE WHEN category_id IN "
                "(SELECT id FROM categories WHERE category_type = 'income') "
                "THEN 'income' ELSE 'expense' END"
            ))


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
