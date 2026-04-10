
import json
import base64
from openai import OpenAI
from config import OPENAI_API_KEY


def _client(api_key=None):
    key = api_key or OPENAI_API_KEY
    return OpenAI(api_key=key)


def _parse_json(text):
    text = text.strip()
    if text.startswith('```'):
        parts = text.split('```')
        text = parts[1] if len(parts) > 1 else text
        if text.startswith('json'):
            text = text[4:]
    try:
        return json.loads(text.strip())
    except Exception:
        return None


def analyze_content(content, memory_type='text', source_url=None, image_path=None, api_key=None):
    client = _client(api_key)

    system = (
        'You are the analysis engine for e-brain, a personal memory and knowledge capture app. '
        'Extract structured information from the given content. '
        'Return ONLY valid JSON — no explanation, no markdown fences.\n\n'
        'JSON shape:\n'
        '{\n'
        '  "title": "short title, 6 words max",\n'
        '  "summary": "2-3 sentences capturing all key information",\n'
        '  "hashtags": ["lowercase","no","hash","symbol","8-15","tags"],\n'
        '  "entities": [{"type":"person|company|technology|concept|location|event","name":"Full Name"}],\n'
        '  "sentiment": "positive|negative|neutral|mixed",\n'
        '  "key_insights": ["insight 1","insight 2"],\n'
        '  "action_items": ["action if any"]\n'
        '}\n\n'
        'Hashtag rules:\n'
        '- All lowercase, no spaces, no # symbol, only letters and digits\n'
        '- Be specific and comprehensive: include topic, category, industry, entity, context tags\n'
        '- Minimum 8, ideally 12-15 hashtags\n'
        '- Examples: venturecapital, deeptech, startup, learning, businessidea, technology\n\n'
        'Return ONLY the JSON object.'
    )

    user_text = (
        f'Memory type: {memory_type}\n'
        f'{("Source URL: " + source_url) if source_url else ""}\n\n'
        f'Content:\n{content}'
    )

    messages = [{'role': 'system', 'content': system}]

    if image_path:
        try:
            with open(image_path, 'rb') as f:
                img_b64 = base64.b64encode(f.read()).decode()
            ext = image_path.rsplit('.', 1)[-1].lower()
            media_map = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
                         'gif': 'image/gif', 'webp': 'image/webp', 'bmp': 'image/bmp'}
            media_type = media_map.get(ext, 'image/jpeg')
            messages.append({
                'role': 'user',
                'content': [
                    {'type': 'image_url', 'image_url': {'url': f'data:{media_type};base64,{img_b64}'}},
                    {'type': 'text', 'text': f'First extract ALL visible text from the image (OCR), then analyze it.\n\n{user_text}'}
                ]
            })
        except Exception:
            messages.append({'role': 'user', 'content': user_text})
    else:
        messages.append({'role': 'user', 'content': user_text})

    try:
        response = client.chat.completions.create(
            model='gpt-4o',
            messages=messages,
            response_format={'type': 'json_object'},
            max_tokens=1800,
        )
        result = _parse_json(response.choices[0].message.content)
        if result:
            return result
    except Exception as e:
        print(f'OpenAI analyze error: {e}')

    return {
        'title':        (content or '')[:60],
        'summary':      (content or '')[:300],
        'hashtags':     ['uncategorized'],
        'entities':     [],
        'sentiment':    'neutral',
        'key_insights': [],
        'action_items': []
    }


def extract_search_params(query, api_key=None):
    client = _client(api_key)
    prompt = (
        f'Extract structured search parameters from this natural language query for a personal memory search app.\n\n'
        f'Query: "{query}"\n\n'
        f'Return a JSON object:\n'
        f'{{\n'
        f'  "keywords": ["important","search","words"],\n'
        f'  "hashtags": ["possible","hashtags","to","check","lowercase"],\n'
        f'  "entity_types": ["person|company|technology|concept"],\n'
        f'  "date_filter": {{"type":"none|relative|range","relative":"today|this_week|this_month|this_year|last_7_days|last_30_days","from_date":null,"to_date":null}},\n'
        f'  "memory_types": ["text|image|url|screenshot|note"],\n'
        f'  "semantic_intent": "what the user is really looking for in plain English"\n'
        f'}}'
    )
    try:
        response = client.chat.completions.create(
            model='gpt-4o',
            messages=[{'role': 'user', 'content': prompt}],
            response_format={'type': 'json_object'},
            max_tokens=500,
        )
        result = _parse_json(response.choices[0].message.content)
        if result:
            return result
    except Exception as e:
        print(f'OpenAI search params error: {e}')

    return {
        'keywords': query.split(),
        'hashtags': [],
        'entity_types': [],
        'date_filter': {'type': 'none'},
        'memory_types': [],
        'semantic_intent': query
    }


def rank_memories(query, candidates, api_key=None):
    client = _client(api_key)
    if not candidates:
        return {'relevant_ids': [], 'explanation': 'No memories in database yet.', 'confidence': 'low'}

    blocks = []
    for m in candidates[:60]:
        ht_names = [mh.get('hashtags', {}).get('display_form', '') for mh in m.get('memory_hashtags', []) if mh.get('hashtags')]
        en_names = [me.get('entities', {}).get('name', '')          for me in m.get('memory_entities', [])  if me.get('entities')]
        blocks.append(
            f"[ID:{m['id']}] [{(m.get('memory_type','text')).upper()}] {m.get('created_at','')[:10]}\n"
            f"Title: {m.get('title','')}\n"
            f"Content: {(m.get('content',''))[:200]}\n"
            f"Summary: {(m.get('ai_summary',''))[:150]}\n"
            f"Hashtags: {', '.join(ht_names)}\n"
            f"Entities: {', '.join(en_names)}"
        )

    prompt = (
        f'You are searching a personal memory database.\n\n'
        f'User query: "{query}"\n\n'
        f'Memories:\n{"---".join(blocks)}\n\n'
        f'Find memories that match semantically, not just by exact words. '
        f'Consider vague references, related concepts, date hints, entity hints.\n\n'
        f'Return a JSON object:\n'
        f'{{\n'
        f'  "relevant_ids": ["most-relevant-id-first","..."],\n'
        f'  "explanation": "2-3 sentences about what was found and why",\n'
        f'  "search_terms_used": ["terms","used"],\n'
        f'  "confidence": "high|medium|low"\n'
        f'}}'
    )
    try:
        response = client.chat.completions.create(
            model='gpt-4o',
            messages=[{'role': 'user', 'content': prompt}],
            response_format={'type': 'json_object'},
            max_tokens=800,
        )
        result = _parse_json(response.choices[0].message.content)
        if result:
            return result
    except Exception as e:
        print(f'OpenAI rank error: {e}')

    return {'relevant_ids': [], 'explanation': 'Search could not complete.', 'confidence': 'low'}


def suggest_hashtag_aliases(hashtag_list, api_key=None):
    client = _client(api_key)
    if not hashtag_list:
        return []
    tags_str = ', '.join(hashtag_list[:50])
    prompt = (
        f'Given these hashtags from a personal knowledge base, identify groups that mean the same thing.\n\n'
        f'Hashtags: {tags_str}\n\n'
        f'Return a JSON object with an "aliases" array:\n'
        f'{{\n'
        f'  "aliases": [\n'
        f'    {{"canonical":"venturecapital","aliases":["vc","vcfund","venturefund"]}},\n'
        f'    ...\n'
        f'  ]\n'
        f'}}\n\n'
        f'Only include groups where tags clearly refer to the same concept.'
    )
    try:
        response = client.chat.completions.create(
            model='gpt-4o',
            messages=[{'role': 'user', 'content': prompt}],
            response_format={'type': 'json_object'},
            max_tokens=800,
        )
        result = _parse_json(response.choices[0].message.content)
        if result and 'aliases' in result:
            return result['aliases']
    except Exception as e:
        print(f'OpenAI alias error: {e}')
    return []
