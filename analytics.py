from flask import Blueprint, render_template, jsonify, session
from utils import login_required
from database import get_analytics

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/analytics')
@login_required
def analytics_page():
    uid  = session['user_id']
    data = get_analytics(uid)
    return render_template('analytics.html', data=data)


@analytics_bp.route('/api/analytics')
@login_required
def api_analytics():
    uid  = session['user_id']
    data = get_analytics(uid)
    return jsonify(data)
