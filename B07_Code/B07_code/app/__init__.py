from flask import Flask

from app.config.secure import Config
from app.extensions import db, login_manager


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Import entities so SQLAlchemy discovers them
    __import__("app.entity")

    # Register all boundary blueprints
    from app.boundary.auth_boundary import auth_bp
    from app.boundary.admin_boundary import admin_bp
    from app.boundary.consultant_boundary import consultant_bp
    from app.boundary.mentor_boundary import mentor_bp
    from app.boundary.coordinator_boundary import coordinator_bp
    from app.boundary.student_boundary import student_bp
    from app.boundary.message_boundary import message_bp
    from app.boundary.appointment_boundary import appointment_bp
    from app.boundary.report_boundary import report_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(consultant_bp)
    app.register_blueprint(mentor_bp)
    app.register_blueprint(coordinator_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(message_bp)
    app.register_blueprint(appointment_bp)
    app.register_blueprint(report_bp)

    @login_manager.user_loader
    def load_user(user_id):
        from app.entity.user import User
        return User.query.get(int(user_id))

    return app
