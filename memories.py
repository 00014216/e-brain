
from flask import Blueprint, render_template, request, jsonify, session
from utils import login_required
from database import get_memories, get_memory, delete_memory, get_hashtags_for_user

memories_bp = Blueprint('memories', __name__)


@memories_bp.route('/memories')
@login_required
def memories_page():
    uid      = session['user_id']
    hashtags = get_hashtags_for_user(uid)
    return render_template('memories.html', hashtags=hashtags)


@memories_bp.route('/api/memories')
@login_required
def api_memories():
    uid         = session['user_id']
    search      = request.args.get('search', '').strip()
    hashtag     = request.args.get('hashtag', '').strip()
    entity_id   = request.args.get('entity_id', '').strip()
    memory_type = request.args.get('type', '').strip()
    date_from   = request.args.get('date_from', '').strip()
    date_to     = request.args.get('date_to', '').strip()
    limit       = int(request.args.get('limit', 60))
    offset      = int(request.args.get('offset', 0))

    rows = get_memories(
        user_id     = uid,
        search      = search or None,
        hashtag     = hashtag or None,
        entity_id   = entity_id or None,
        memory_type = memory_type or None,
        date_from   = date_from or None,
        date_to     = date_to or None,
        limit       = limit,
        offset      = offset,
    )
    return jsonify({'memories': rows, 'count': len(rows)})


@memories_bp.route('/api/memories/<memory_id>')
@login_required
def api_memory_detail(memory_id):
    uid = session['user_id']
    mem = get_memory(uid, memory_id)
    if not mem:
        return jsonify({'error': 'Memory not found'}), 404
    return jsonify({'memory': mem})


@memories_bp.route('/api/memories/<memory_id>', methods=['DELETE'])
@login_required
def api_delete_memory(memory_id):
    uid = session['user_id']
    ok  = delete_memory(uid, memory_id)
    if ok:
        return jsonify({'success': True})
    return jsonify({'error': 'Could not delete memory'}), 404


@memories_bp.route('/api/memories/<memory_id>/add-hashtag', methods=['POST'])
@login_required
def api_add_hashtag_to_memory(memory_id):
    uid  = session['user_id']
    body = request.get_json() or {}
    tag  = (body.get('hashtag') or '').strip().lstrip('#')
    if not tag:
        return jsonify({'error': 'Hashtag required'}), 400
    mem = get_memory(uid, memory_id)
    if not mem:
        return jsonify({'error': 'Memory not found'}), 404
    from database import get_client, get_or_create_hashtag, normalize_hashtag
    db   = get_client()
    norm = normalize_hashtag(tag)
    hid  = get_or_create_hashtag(db, norm, tag)
    if not hid:
        return jsonify({'error': 'Could not create hashtag'}), 500
    try:
        db.table('memory_hashtags').insert({'memory_id': memory_id, 'hashtag_id': hid}).execute()
    except Exception:
        pass  # already linked
    return jsonify({'success': True, 'normalized': norm, 'display': tag})


@memories_bp.route('/memory/<memory_id>')
@login_required
def memory_detail_page(memory_id):
    uid = session['user_id']
    mem = get_memory(uid, memory_id)
    if not mem:
        from flask import abort
        abort(404)
    return render_template('memory_detail.html', memory=mem)
