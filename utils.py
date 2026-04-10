from functools import wraps
from flask import session, redirect, url_for, request, jsonify


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Not authenticated'}), 401
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def allowed_file(filename):
    from config import ALLOWED_EXTENSIONS
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
