from flask import Flask
from admin_dashboard import admin_dashboard_bp

app = Flask(__name__)
app.secret_key = 'admin_secret_key'
app.register_blueprint(admin_dashboard_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=False)
