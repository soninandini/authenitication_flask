

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

from routes import app as routes_app
from models import db  # Importing db from models

migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    migrate.init_app(app, db)
    jwt = JWTManager(app)

    app.register_blueprint(routes_app)

  
    with app.app_context():  
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
