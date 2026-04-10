
import os
from flask import Blueprint, render_template, request, jsonify, session
from utils import login_required, allowed_file
from database import create_memory, get_memories, get_settings
from ai_client import analyze_content
from url_scraper import scrape_url
from image_handler import save_upload, resize_for_storage
from config import UPLOAD_FOLDER

capture_bp = Blueprint('capture', __name__)


@capture_bp.route('/capture')
@login_required
def capture_page():
    uid    = session['user_id']
    recent = get_memories(uid, limit=5)
    return render_template('capture.html', recent=recent)


@capture_bp.route('/api/capture', methods=['POST'])
@login_required
def api_capture():
    uid         = session['user_id']
    content     = request.form.get('content', '').strip()
    source_url  = request.form.get('source_url', '').strip()
    memory_type = request.form.get('memory_type', 'text')
    user_note   = request.form.get('user_note', '').strip()

    settings    = get_settings(uid)
    api_key     = settings.get('openai_api_key') or None

    image_path  = None

    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            path, err = save_upload(file, UPLOAD_FOLDER)
            if err:
                return jsonify({'error': err}), 400
            resize_for_storage(path)
            image_path  = path
            memory_type = 'image' if memory_type == 'text' else memory_type

    if source_url and not content and not image_path:
        scraped     = scrape_url(source_url)
        memory_type = 'url'
        content = (
            f"URL: {scraped['url']}\n"
            f"Title: {scraped['title']}\n"
            f"Author: {scraped['author']}\n"
            f"Published: {scraped['pub_date']}\n\n"
            f"{scraped['content']}"
        )
    elif source_url and content:
        content = f"[Source: {source_url}]\n\n{content}"

    if user_note:
        content = f"{content}\n\n[User note]: {user_note}" if content else f"[User note]: {user_note}"

    if not content and not image_path:
        return jsonify({'error': 'Nothing to capture. Add text, a URL, or an image.'}), 400

    analysis = analyze_content(
        content=content or '',
        memory_type=memory_type,
        source_url=source_url or None,
        image_path=image_path,
        api_key=api_key
    )

    if image_path and not content:
        content = analysis.get('summary', 'Image captured')

    data = {
        'content':      content,
        'raw_content':  content,
        'memory_type':  memory_type,
        'source_url':   source_url,
        'source_title': analysis.get('title', ''),
        'title':        analysis.get('title', ''),
        'image_path':   image_path or '',
        'ai_summary':   analysis.get('summary', ''),
        'hashtags':     analysis.get('hashtags', []),
        'entities':     analysis.get('entities', []),
        'sentiment':    analysis.get('sentiment', 'neutral'),
        'key_insights': analysis.get('key_insights', []),
        'action_items': analysis.get('action_items', []),
    }

    saved = create_memory(uid, data)
    if saved:
        return jsonify({
            'success':  True,
            'memory':   saved,
            'analysis': analysis
        })
    return jsonify({'error': 'Failed to save memory.'}), 500
