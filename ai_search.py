
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, session
from utils import login_required
from database import get_memories, get_all_memories_for_search, get_settings
from ai_client import extract_search_params, rank_memories

ai_bp = Blueprint('ai', __name__)


def _apply_date_filter(df):
    now   = datetime.utcnow()
    dtype = (df or {}).get('type', 'none')

    if dtype == 'relative':
        rel = df.get('relative', '')
        offsets = {
            'today':        timedelta(days=0),
            'this_week':    timedelta(days=7),
            'this_month':   timedelta(days=30),
            'this_year':    timedelta(days=365),
            'last_7_days':  timedelta(days=7),
            'last_30_days': timedelta(days=30),
        }
        delta = offsets.get(rel)
        if delta is not None:
            return (now - delta).isoformat(), now.isoformat()

    if dtype == 'range':
        return df.get('from_date'), df.get('to_date')

    if dtype == 'specific':
        d = df.get('from_date')
        if d:
            return d, d + 'T23:59:59'

    return None, None


@ai_bp.route('/ai')
@login_required
def ai_page():
    return render_template('ai.html')


@ai_bp.route('/api/ai/search', methods=['POST'])
@login_required
def api_ai_search():
    uid      = session['user_id']
    body     = request.get_json() or {}
    query    = (body.get('query') or '').strip()

    if not query:
        return jsonify({'error': 'Query is required'}), 400

    settings = get_settings(uid)
    api_key  = settings.get('openai_api_key') or None

    params     = extract_search_params(query, api_key=api_key)
    date_from, date_to = _apply_date_filter(params.get('date_filter'))

    memory_type = None
    mtypes = params.get('memory_types', [])
    if len(mtypes) == 1:
        memory_type = mtypes[0]

    candidates = get_all_memories_for_search(uid)

    if date_from:
        candidates = [m for m in candidates if m.get('created_at', '') >= date_from]
    if date_to:
        candidates = [m for m in candidates if m.get('created_at', '') <= date_to]
    if memory_type:
        candidates = [m for m in candidates if m.get('memory_type') == memory_type]

    keywords = params.get('keywords', [])
    hashtags = params.get('hashtags', [])

    if keywords or hashtags:
        keyword_set = [k.lower() for k in keywords]
        scored = []
        for m in candidates:
            text = ' '.join([
                m.get('title', ''),
                m.get('content', ''),
                m.get('ai_summary', ''),
            ]).lower()
            ht_norms = [mh.get('hashtags', {}).get('normalized_form', '') for mh in m.get('memory_hashtags', [])]
            score = sum(1 for kw in keyword_set if kw in text)
            score += sum(2 for ht in hashtags if ht in ht_norms)
            scored.append((score, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        candidates = [m for _, m in scored]

    ranked = rank_memories(query, candidates[:50], api_key=api_key)

    relevant_ids = ranked.get('relevant_ids', [])
    id_order     = {rid: i for i, rid in enumerate(relevant_ids)}
    result_map   = {m['id']: m for m in candidates}

    ordered = []
    for rid in relevant_ids:
        if rid in result_map:
            ordered.append(result_map[rid])
    for m in candidates:
        if m['id'] not in id_order and len(ordered) < 20:
            ordered.append(m)

    return jsonify({
        'memories':    ordered[:20],
        'explanation': ranked.get('explanation', ''),
        'confidence':  ranked.get('confidence', 'low'),
        'params':      params,
    })


@ai_bp.route('/api/ai/quick-search')
@login_required
def api_quick_search():
    uid   = session['user_id']
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'memories': []})

    rows = get_memories(uid, search=query, limit=10)
    return jsonify({'memories': rows})
