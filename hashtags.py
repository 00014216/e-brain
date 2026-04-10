
from flask import Blueprint, render_template, request, jsonify, session
from utils import login_required
from database import (get_hashtags_for_user, get_memories, add_hashtag_alias,
                      normalize_hashtag)
from ai_client import suggest_hashtag_aliases

hashtags_bp = Blueprint('hashtags', __name__)


@hashtags_bp.route('/hashtags')
@login_required
def hashtags_page():
    uid  = session['user_id']
    tags = get_hashtags_for_user(uid)
    return render_template('hashtags_view.html', hashtags=tags)


@hashtags_bp.route('/api/hashtags')
@login_required
def api_hashtags():
    uid  = session['user_id']
    tags = get_hashtags_for_user(uid)
    return jsonify({'hashtags': tags})


@hashtags_bp.route('/api/hashtags/memories')
@login_required
def api_hashtag_memories():
    uid     = session['user_id']
    hashtag = request.args.get('tag', '').strip()
    if not hashtag:
        return jsonify({'memories': []})
    rows = get_memories(uid, hashtag=hashtag, limit=50)
    return jsonify({'memories': rows, 'hashtag': hashtag})


@hashtags_bp.route('/api/hashtags/suggest-aliases', methods=['POST'])
@login_required
def api_suggest_aliases():
    uid  = session['user_id']
    tags = get_hashtags_for_user(uid)
    tag_names = [t['normalized_form'] for t in tags]

    from database import get_settings
    settings = get_settings(uid)
    api_key  = settings.get('openai_api_key') or None

    suggestions = suggest_hashtag_aliases(tag_names, api_key=api_key)
    return jsonify({'suggestions': suggestions})


@hashtags_bp.route('/api/hashtags/add-alias', methods=['POST'])
@login_required
def api_add_alias():
    body      = request.get_json() or {}
    canonical = normalize_hashtag(body.get('canonical', ''))
    alias     = normalize_hashtag(body.get('alias', ''))
    if not canonical or not alias:
        return jsonify({'error': 'canonical and alias required'}), 400
    ok = add_hashtag_alias(canonical, alias)
    if ok:
        return jsonify({'success': True})
    return jsonify({'error': 'Could not add alias. Make sure canonical hashtag exists.'}), 400
