
import os
from flask import Flask, redirect, url_for, session
from config import SECRET_KEY, UPLOAD_FOLDER, MAX_CONTENT_LENGTH

from auth            import auth_bp
from capture         import capture_bp
from memories        import memories_bp
from ai_search       import ai_bp
from hashtags        import hashtags_bp
from entities        import entities_bp
from analytics       import analytics_bp
from settings_routes import settings_bp

app = Flask(__name__)
app.secret_key             = SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['UPLOAD_FOLDER']      = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.register_blueprint(auth_bp)
app.register_blueprint(capture_bp)
app.register_blueprint(memories_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(hashtags_bp)
app.register_blueprint(entities_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(settings_bp)


@app.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('capture.capture_page'))
    return redirect(url_for('auth.login'))


@app.errorhandler(404)
def not_found(e):
    return redirect(url_for('capture.capture_page')), 302


@app.errorhandler(413)
def too_large(e):
    from flask import jsonify
    return jsonify({'error': 'File too large. Maximum size is 20 MB.'}), 413


if __name__ == '__main__':
    app.run(debug=True, port=5000)
