from flask import Blueprint, render_template, request, jsonify, session
from utils import login_required
from database import get_entities, get_memories_for_entity

entities_bp = Blueprint('entities', __name__)

ENTITY_TYPES = ['person', 'company', 'technology', 'concept', 'location', 'event', 'other']


@entities_bp.route('/entities')
@login_required
def entities_page():
    uid      = session['user_id']
    all_ents = get_entities(uid)
    grouped  = {et: [] for et in ENTITY_TYPES}
    for e in all_ents:
        et = e.get('entity_type', 'other')
        grouped.setdefault(et, []).append(e)
    return render_template('entities_view.html', entities=all_ents, grouped=grouped, types=ENTITY_TYPES)


@entities_bp.route('/api/entities')
@login_required
def api_entities():
    uid         = session['user_id']
    entity_type = request.args.get('type', '').strip()
    rows        = get_entities(uid, entity_type=entity_type or None)
    return jsonify({'entities': rows})


@entities_bp.route('/api/entities/<entity_id>/memories')
@login_required
def api_entity_memories(entity_id):
    uid  = session['user_id']
    rows = get_memories_for_entity(uid, entity_id)
    return jsonify({'memories': rows, 'entity_id': entity_id})
