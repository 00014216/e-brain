from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_ANON_KEY
from database import save_settings

auth_bp = Blueprint('auth', __name__)


def _auth_client():
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('capture.capture_page'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Email and password are required.', 'error')
            return render_template('login.html')

        try:
            client   = _auth_client()
            response = client.auth.sign_in_with_password({'email': email, 'password': password})
            user     = response.user

            if user:
                session['user_id'] = user.id
                session['email']   = user.email
                session.permanent  = True
                return redirect(url_for('capture.capture_page'))
            else:
                flash('Invalid email or password.', 'error')
        except Exception as e:
            msg = str(e)
            if 'Invalid login' in msg or 'invalid' in msg.lower():
                flash('Invalid email or password.', 'error')
            else:
                flash('Login failed. Please try again.', 'error')

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('capture.capture_page'))

    if request.method == 'POST':
        email        = request.form.get('email', '').strip()
        password     = request.form.get('password', '')
        confirm      = request.form.get('confirm_password', '')
        display_name = request.form.get('display_name', '').strip()

        if not email or not password:
            flash('Email and password are required.', 'error')
            return render_template('register.html')

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')

        try:
            client   = _auth_client()
            response = client.auth.sign_up({'email': email, 'password': password})
            user     = response.user

            if user:
                save_settings(user.id, {'display_name': display_name or email.split('@')[0]})
                session['user_id'] = user.id
                session['email']   = user.email
                session.permanent  = True
                flash('Account created! Welcome to e-brain.', 'success')
                return redirect(url_for('capture.capture_page'))
            else:
                flash('Registration failed. Email may already be in use.', 'error')
        except Exception as e:
            msg = str(e)
            if 'already' in msg.lower() or 'registered' in msg.lower():
                flash('An account with this email already exists.', 'error')
            else:
                flash('Registration failed. Please try again.', 'error')

    return render_template('register.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
