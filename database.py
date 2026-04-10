
import re
from datetime import datetime, timedelta
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY


def get_client():
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def normalize_hashtag(tag):
    tag = tag.strip().lstrip('#').lower()
    tag = re.sub(r'[^a-z0-9]', '', tag)
    return tag


def normalize_entity_name(name):
    return re.sub(r'[^a-z0-9]', '', name.lower())


#memories

def create_memory(user_id, data):
    db = get_client()
    row = {
        'user_id':      user_id,
        'title':        data.get('title', ''),
        'content':      data.get('content', ''),
        'raw_content':  data.get('raw_content', ''),
        'memory_type':  data.get('memory_type', 'text'),
        'source_url':   data.get('source_url', ''),
        'source_title': data.get('source_title', ''),
        'source_author':data.get('source_author', ''),
        'image_url':    data.get('image_url', ''),
        'image_path':   data.get('image_path', ''),
        'ai_summary':   data.get('ai_summary', ''),
        'ai_analysis':  data.get('ai_analysis', ''),
        'sentiment':    data.get('sentiment', 'neutral'),
        'key_insights': data.get('key_insights', []),
        'action_items': data.get('action_items', []),
    }
    result = db.table('memories').insert(row).execute()
    if not result.data:
        return None
    memory_id = result.data[0]['id']
    _link_hashtags(db, memory_id, data.get('hashtags', []))
    _link_entities(db, memory_id, user_id, data.get('entities', []))
    return result.data[0]


def get_memories(user_id, search=None, hashtag=None, entity_id=None,
                 memory_type=None, date_from=None, date_to=None,
                 limit=60, offset=0):
    db = get_client()
    q = (db.table('memories')
           .select('id,title,content,memory_type,source_url,source_title,image_url,ai_summary,sentiment,key_insights,action_items,created_at,'
                   'memory_hashtags(hashtag_id,hashtags(id,normalized_form,display_form)),'
                   'memory_entities(entity_id,entities(id,name,entity_type))')
           .eq('user_id', user_id)
           .order('created_at', desc=True)
           .limit(limit)
           .offset(offset))

    if memory_type:
        q = q.eq('memory_type', memory_type)
    if date_from:
        q = q.gte('created_at', date_from)
    if date_to:
        q = q.lte('created_at', date_to)

    rows = q.execute().data or []

    if search:
        s = search.lower()
        rows = [r for r in rows if
                s in (r.get('title') or '').lower() or
                s in (r.get('content') or '').lower() or
                s in (r.get('ai_summary') or '')]

    if hashtag:
        norm = normalize_hashtag(hashtag)
        canonical = _resolve_canonical(db, norm)
        rows = [r for r in rows if
                any(_ht(mh) == canonical for mh in r.get('memory_hashtags', []))]

    if entity_id:
        rows = [r for r in rows if
                any(me.get('entity_id') == entity_id
                    for me in r.get('memory_entities', []))]

    return rows


def get_memory(user_id, memory_id):
    db = get_client()
    result = (db.table('memories')
                .select('*,'
                        'memory_hashtags(hashtag_id,hashtags(id,normalized_form,display_form)),'
                        'memory_entities(entity_id,entities(id,name,entity_type))')
                .eq('id', memory_id)
                .eq('user_id', user_id)
                .execute())
    return result.data[0] if result.data else None


def delete_memory(user_id, memory_id):
    db = get_client()
    db.table('memory_hashtags').delete().eq('memory_id', memory_id).execute()
    db.table('memory_entities').delete().eq('memory_id', memory_id).execute()
    r = db.table('memories').delete().eq('id', memory_id).eq('user_id', user_id).execute()
    return bool(r.data)


def get_all_memories_for_search(user_id):
    db = get_client()
    result = (db.table('memories')
                .select('id,title,content,ai_summary,memory_type,created_at,'
                        'memory_hashtags(hashtags(normalized_form,display_form)),'
                        'memory_entities(entities(name,entity_type))')
                .eq('user_id', user_id)
                .order('created_at', desc=True)
                .execute())
    return result.data or []


#chashtags

def _ht(mh):
    h = mh.get('hashtags') or {}
    return h.get('normalized_form', '')


def _resolve_canonical(db, normalized):
    alias = db.table('hashtag_aliases').select('canonical_hashtag_id,hashtags(normalized_form)').eq('alias_normalized', normalized).execute()
    if alias.data:
        return alias.data[0].get('hashtags', {}).get('normalized_form', normalized)
    return normalized


def get_or_create_hashtag(db, normalized, display):
    if not normalized:
        return None
    canonical = _resolve_canonical(db, normalized)
    ex = db.table('hashtags').select('id').eq('normalized_form', canonical).execute()
    if ex.data:
        hid = ex.data[0]['id']
        cnt = db.table('hashtags').select('usage_count').eq('id', hid).execute().data[0]['usage_count']
        db.table('hashtags').update({'usage_count': cnt + 1}).eq('id', hid).execute()
        return hid
    r = db.table('hashtags').insert({'normalized_form': normalized, 'display_form': display, 'usage_count': 1}).execute()
    return r.data[0]['id'] if r.data else None


def _link_hashtags(db, memory_id, hashtag_list):
    for tag in hashtag_list:
        norm = normalize_hashtag(tag)
        if not norm:
            continue
        hid = get_or_create_hashtag(db, norm, tag.lstrip('#'))
        if hid:
            try:
                db.table('memory_hashtags').insert({'memory_id': memory_id, 'hashtag_id': hid}).execute()
            except Exception:
                pass


def get_hashtags_for_user(user_id):
    db = get_client()
    mem_r = db.table('memories').select('id').eq('user_id', user_id).execute()
    if not mem_r.data:
        return []
    mem_ids = [m['id'] for m in mem_r.data]

    chunk_size = 100
    hashtag_map = {}
    for i in range(0, len(mem_ids), chunk_size):
        chunk = mem_ids[i:i + chunk_size]
        mh_r = (db.table('memory_hashtags')
                  .select('memory_id,hashtag_id,hashtags(id,normalized_form,display_form)')
                  .in_('memory_id', chunk)
                  .execute())
        for mh in (mh_r.data or []):
            h = mh.get('hashtags') or {}
            hid = h.get('id')
            if hid:
                if hid not in hashtag_map:
                    hashtag_map[hid] = {**h, 'count': 0, 'memory_ids': []}
                hashtag_map[hid]['count'] += 1
                hashtag_map[hid]['memory_ids'].append(mh['memory_id'])

    return sorted(hashtag_map.values(), key=lambda x: x['count'], reverse=True)


def add_hashtag_alias(canonical_normalized, alias_normalized):
    db = get_client()
    canon = db.table('hashtags').select('id').eq('normalized_form', canonical_normalized).execute()
    if not canon.data:
        return False
    try:
        db.table('hashtag_aliases').insert({
            'canonical_hashtag_id': canon.data[0]['id'],
            'alias_normalized': alias_normalized
        }).execute()
        return True
    except Exception:
        return False


#entities

def get_or_create_entity(db, user_id, entity_type, name):
    norm = normalize_entity_name(name)
    if not norm:
        return None
    ex = db.table('entities').select('id,mention_count').eq('user_id', user_id).eq('normalized_name', norm).execute()
    if ex.data:
        eid = ex.data[0]['id']
        db.table('entities').update({'mention_count': ex.data[0]['mention_count'] + 1}).eq('id', eid).execute()
        return eid
    r = db.table('entities').insert({
        'user_id': user_id,
        'entity_type': entity_type,
        'name': name,
        'normalized_name': norm,
        'mention_count': 1
    }).execute()
    return r.data[0]['id'] if r.data else None


def _link_entities(db, memory_id, user_id, entity_list):
    for entity in entity_list:
        etype = entity.get('type', 'other')
        name  = (entity.get('name') or '').strip()
        if not name:
            continue
        eid = get_or_create_entity(db, user_id, etype, name)
        if eid:
            try:
                db.table('memory_entities').insert({'memory_id': memory_id, 'entity_id': eid}).execute()
            except Exception:
                pass


def get_entities(user_id, entity_type=None):
    db = get_client()
    q = (db.table('entities')
           .select('*')
           .eq('user_id', user_id)
           .order('mention_count', desc=True))
    if entity_type:
        q = q.eq('entity_type', entity_type)
    return q.execute().data or []


def get_memories_for_entity(user_id, entity_id):
    db = get_client()
    me_r = db.table('memory_entities').select('memory_id').eq('entity_id', entity_id).execute()
    if not me_r.data:
        return []
    mids = [r['memory_id'] for r in me_r.data]
    r = (db.table('memories')
           .select('id,title,content,memory_type,created_at,ai_summary')
           .eq('user_id', user_id)
           .in_('id', mids)
           .order('created_at', desc=True)
           .execute())
    return r.data or []


# analytics

def get_analytics(user_id):
    db = get_client()
    all_mems = db.table('memories').select('id,memory_type,created_at,sentiment').eq('user_id', user_id).execute().data or []
    total = len(all_mems)

    type_counts = {}
    sentiment_counts = {}
    for m in all_mems:
        t = m.get('memory_type', 'text')
        s = m.get('sentiment', 'neutral')
        type_counts[t]      = type_counts.get(t, 0) + 1
        sentiment_counts[s] = sentiment_counts.get(s, 0) + 1

    now = datetime.utcnow()
    recent_7  = sum(1 for m in all_mems if m['created_at'] >= (now - timedelta(days=7)).isoformat())
    recent_30 = sum(1 for m in all_mems if m['created_at'] >= (now - timedelta(days=30)).isoformat())

    daily = {}
    for m in all_mems:
        day = m['created_at'][:10]
        daily[day] = daily.get(day, 0) + 1

    sorted_days = sorted(daily.items())[-30:]

    top_hashtags = get_hashtags_for_user(user_id)[:10]
    top_entities = get_entities(user_id)[:10]

    return {
        'total':           total,
        'type_counts':     type_counts,
        'sentiment_counts':sentiment_counts,
        'recent_7_days':   recent_7,
        'recent_30_days':  recent_30,
        'daily_activity':  sorted_days,
        'top_hashtags':    top_hashtags,
        'top_entities':    top_entities,
    }


# settigns

def get_settings(user_id):
    db = get_client()
    r = db.table('user_settings').select('*').eq('user_id', user_id).execute()
    return r.data[0] if r.data else {}


def save_settings(user_id, data):
    db = get_client()
    payload = {
        'user_id':           user_id,
        'display_name':      data.get('display_name', ''),
        'anthropic_api_key': data.get('anthropic_api_key', ''),
        'openai_api_key':    data.get('openai_api_key', ''),
        'updated_at':        datetime.utcnow().isoformat(),
    }
    ex = db.table('user_settings').select('user_id').eq('user_id', user_id).execute()
    if ex.data:
        db.table('user_settings').update(payload).eq('user_id', user_id).execute()
    else:
        db.table('user_settings').insert(payload).execute()
