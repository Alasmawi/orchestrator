import logging
import os
import time

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import URL
from sqlalchemy.exc import OperationalError

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    # The audit's curl examples use trailing slashes (/api/movies/); accept both forms.
    app.url_map.strict_slashes = False

    # URL.create escapes special characters in the password.
    app.config["SQLALCHEMY_DATABASE_URI"] = URL.create(
        "postgresql",
        username=os.environ["INVENTORY_DB_USER"],
        password=os.environ["INVENTORY_DB_PASSWORD"],
        host=os.environ["INVENTORY_DB_HOST"],
        port=int(os.environ.get("INVENTORY_DB_PORT", 5432)),
        database=os.environ["INVENTORY_DB_NAME"],
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # Drop pooled connections that died when the database pod restarted or moved.
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}

    db.init_app(app)

    from app.routes import movies_bp

    app.register_blueprint(movies_bp)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    # The database may still be starting (or just moved nodes): wait instead of crashing.
    with app.app_context():
        while True:
            try:
                db.create_all()
                break
            except OperationalError:
                logging.getLogger("inventory-db").warning("inventory-db not reachable yet, retrying in 3s...")
                time.sleep(3)

    return app
