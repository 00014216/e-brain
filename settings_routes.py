from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from utils import login_required
from database import get_settings, save_settings

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings_page():
    uid      = session['user_id']
    current  = get_settings(uid)

    if request.method == 'POST':
        data = {
            'display_name':      request.form.get('display_name', '').strip(),
            'anthropic_api_key': request.form.get('anthropic_api_key', '').strip(),
            'openai_api_key':    request.form.get('openai_api_key', '').strip(),
        }
        save_settings(uid, data)
        flash('Settings saved.', 'success')
        return redirect(url_for('settings.settings_page'))

    return render_template('settings.html', settings=current, email=session.get('email', ''))


@settings_bp.route('/api/settings', methods=['GET'])
@login_required
def api_get_settings():
    uid  = session['user_id']
    data = get_settings(uid)
    safe = {k: v for k, v in data.items() if k not in ('anthropic_api_key', 'openai_api_key')}
    safe['has_anthropic_key'] = bool(data.get('anthropic_api_key'))
    safe['has_openai_key']    = bool(data.get('openai_api_key'))
    return jsonify(safe)


@settings_bp.route('/api/settings', methods=['POST'])
@login_required
def api_save_settings():
    uid  = session['user_id']
    body = request.get_json() or {}
    save_settings(uid, body)
    return jsonify({'success': True})
