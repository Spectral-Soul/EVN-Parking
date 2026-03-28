import os
from flask import Flask, render_template, g, session, redirect, url_for
from db import close_db, init_db, get_db
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.teardown_appcontext(close_db)

    # Initialize DB (creates tables if not exist, seeds if empty)
    with app.app_context():
        init_db()
        from services.seeder import seed_database
        seed_database()

    # Register Blueprints
    from routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from routes.parking import bp as parking_bp
    app.register_blueprint(parking_bp, url_prefix='/api/parking')

    from routes.booking import bp as booking_bp
    app.register_blueprint(booking_bp, url_prefix='/api/booking')

    from routes.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from routes.ai import bp as ai_bp
    app.register_blueprint(ai_bp, url_prefix='/api/ai')

    # Frontend Routes
    @app.route('/')
    def index():
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('index.html')

    @app.route('/login')
    def login_page():
        return render_template('auth.html')

    @app.route('/admin_dashboard')
    def admin_page():
        if 'user_id' not in session or not session.get('is_admin'):
            return redirect(url_for('index'))
        return render_template('admin.html')
        
    @app.route('/bookings')
    def bookings_page():
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('bookings.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
