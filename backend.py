"""
FocusFlow-AI Backend - FREE AI Edition
=======================================
Works with Google Gemini or Groq (both 100% FREE)
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import json
import os
import logging
from datetime import datetime, timedelta
from functools import wraps
from contextlib import contextmanager

# Try to import AI libraries
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠ google-generativeai not installed. Run: pip install google-generativeai")

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠ groq not installed. Run: pip install groq")

# ================================
# LOGGING
# ================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================================
# CONFIGURATION
# ================================

class Config:
    DATABASE = 'focusflow.db'
    
    # Check for API keys
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    
    # Determine AI provider
    AI_PROVIDER = None
    AI_MODEL = None
    
    if GEMINI_API_KEY and GEMINI_AVAILABLE:
        AI_PROVIDER = 'gemini'
        AI_MODEL = 'gemini-2.5-flash'
    elif GROQ_API_KEY and GROQ_AVAILABLE:
        AI_PROVIDER = 'groq'
        AI_MODEL = 'llama3-8b-8192'
    
    AI_ENABLED = AI_PROVIDER is not None
    
    PORT = int(os.getenv('PORT', 5000))

config = Config()

# ================================
# FLASK APP
# ================================

app = Flask(__name__, static_folder='.')
CORS(app)

# Initialize AI
ai_client = None

if config.AI_PROVIDER == 'gemini':
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        ai_client = genai.GenerativeModel('gemini-2.5-flash')
        logger.info("✓ AI: Google Gemini (FREE)")
    except Exception as e:
        logger.error(f"Gemini setup failed: {e}")
        config.AI_ENABLED = False

elif config.AI_PROVIDER == 'groq':
    try:
        ai_client = Groq(api_key=config.GROQ_API_KEY)
        logger.info("✓ AI: Groq (FREE)")
    except Exception as e:
        logger.error(f"Groq setup failed: {e}")
        config.AI_ENABLED = False

if not config.AI_ENABLED:
    logger.info("✓ AI: Fallback mode (no API needed)")

# ================================
# DATABASE
# ================================

@contextmanager
def get_db():
    conn = sqlite3.connect(config.DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db() as db:
        cursor = db.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            week_start DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS study_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_id INTEGER NOT NULL,
            day_of_week INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            subject TEXT NOT NULL,
            topic TEXT,
            priority TEXT DEFAULT 'medium',
            completed BOOLEAN DEFAULT 0
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            type TEXT DEFAULT 'goal',
            parent_id INTEGER,
            priority TEXT DEFAULT 'medium',
            completed BOOLEAN DEFAULT 0
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            workflow_text TEXT NOT NULL,
            generated_schedule_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

init_db()

# ================================
# HELPERS
# ================================

def sanitize(text, max_len=1000):
    return (text or "").strip()[:max_len]

def get_or_create_user(username='demo_user'):
    username = sanitize(username, 50) or 'demo_user'
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        if not user:
            cursor.execute('INSERT INTO users (username) VALUES (?)', (username,))
            return cursor.lastrowid
        return user[0]

def require_user(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        username = request.headers.get('X-User', 'demo_user')
        user_id = get_or_create_user(username)
        return f(user_id, *args, **kwargs)
    return decorated

# ================================
# AI FUNCTIONS
# ================================

def get_ai_chat_response(message, history):
    """Get AI chat response"""
    if config.AI_PROVIDER == 'gemini':
        try:
            chat_history = []
            for h in history[:-1]:
                role = "user" if h['role'] == 'user' else "model"
                chat_history.append({"role": role, "parts": [h['content']]})
            
            chat = ai_client.start_chat(history=chat_history)
            
            prompt = f"""You are FocusFlow AI, a study scheduling assistant for students.

Help students:
- Optimize study schedules
- Provide actionable time management advice
- Suggest effective study techniques
- Be encouraging and supportive

Keep responses brief (2-3 sentences) unless detail is requested.

Student: {message}"""
            
            response = chat.send_message(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return None
    
    elif config.AI_PROVIDER == 'groq':
        try:
            messages = [
                {"role": "system", "content": "You are FocusFlow AI, a helpful study scheduling assistant. Provide concise, actionable advice."}
            ]
            
            for h in history[:-1]:
                messages.append({"role": h['role'], "content": h['content']})
            
            messages.append({"role": "user", "content": message})
            
            response = ai_client.chat.completions.create(
                model=config.AI_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq error: {e}")
            return None
    
    return None

def get_ai_schedule(workflow):
    """Get AI schedule generation"""
    prompt = f"""Generate a study schedule. Return ONLY valid JSON:

{{
  "subjects": [{{"name": "Subject", "priority": "high/medium/low", "hours_per_week": 6}}],
  "study_blocks": [{{"day": 0-6, "start_time": "9:00 AM", "end_time": "11:00 AM", "subject": "Subject", "topic": "Topic", "priority": "high"}}],
  "recommendations": ["tip1", "tip2", "tip3"]
}}

User workflow:
{workflow}"""
    
    if config.AI_PROVIDER == 'gemini':
        try:
            response = ai_client.generate_content(prompt)
            text = response.text
            
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            
            return json.loads(text.strip())
        except Exception as e:
            logger.error(f"Gemini schedule error: {e}")
            return None
    
    elif config.AI_PROVIDER == 'groq':
        try:
            response = ai_client.chat.completions.create(
                model=config.AI_MODEL,
                messages=[
                    {"role": "system", "content": "Generate study schedule. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=2000
            )
            
            text = response.choices[0].message.content
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            
            return json.loads(text.strip())
        except Exception as e:
            logger.error(f"Groq schedule error: {e}")
            return None
    
    return None

def fallback_schedule(workflow):
    """Rule-based schedule"""
    subjects = []
    workflow_lower = workflow.lower()
    
    keywords = {
        'math': 'high', 'mathematics': 'high', 'calculus': 'high',
        'physics': 'medium', 'chemistry': 'medium', 'biology': 'medium',
        'english': 'medium', 'history': 'low', 'programming': 'high'
    }
    
    for kw, pri in keywords.items():
        if kw in workflow_lower:
            subjects.append({'name': kw.capitalize(), 'priority': pri, 'hours_per_week': 6})
    
    if not subjects:
        subjects = [{'name': 'Subject 1', 'priority': 'high', 'hours_per_week': 6}]
    
    prefer_morning = any(k in workflow_lower for k in ['morning', '9', '10', 'early'])
    
    blocks = []
    for i, subj in enumerate(subjects[:3]):
        for day in range(5):
            if day % len(subjects) == i:
                if prefer_morning:
                    start, end = '9:00 AM', '11:00 AM'
                else:
                    start, end = '2:00 PM', '4:00 PM'
                
                blocks.append({
                    'day': day,
                    'start_time': start,
                    'end_time': end,
                    'subject': subj['name'],
                    'topic': 'Study Session',
                    'priority': subj['priority']
                })
    
    return {
        'subjects': subjects,
        'study_blocks': blocks,
        'recommendations': [
            'Focus on high-priority subjects during peak hours',
            'Take 10-15 minute breaks between sessions',
            'Use active recall for better retention'
        ]
    }

# ================================
# ROUTES
# ================================

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/chat', methods=['POST'])
@require_user
def chat(user_id):
    data = request.get_json()
    message = sanitize(data.get('message', ''), 2000)
    if not message:
        return jsonify({'error': 'Message required'}), 400
    
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute('INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)',
                      (user_id, 'user', message))
        cursor.execute('SELECT role, content FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10',
                      (user_id,))
        history = list(reversed(cursor.fetchall()))
    
    ai_response = None
    if config.AI_ENABLED:
        ai_response = get_ai_chat_response(message, history)
    
    if not ai_response:
        fallbacks = [
            "Focus on high-priority subjects during peak concentration hours. Would you like help creating a schedule?",
            "Try the Pomodoro Technique: 25 minutes of focused work followed by a 5-minute break.",
            "Create a balanced schedule alternating between subjects to prevent burnout.",
            "Active recall and spaced repetition are proven effective. Would you like help incorporating these?",
        ]
        ai_response = fallbacks[len(history) % len(fallbacks)]
    
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute('INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)',
                      (user_id, 'assistant', ai_response))
    
    return jsonify({'response': ai_response, 'timestamp': datetime.now().isoformat()})

@app.route('/api/chat/history', methods=['GET'])
@require_user
def get_chat_history(user_id):
    limit = min(int(request.args.get('limit', 50)), 200)
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute('SELECT role, content, timestamp FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?',
                      (user_id, limit))
        history = [dict(row) for row in cursor.fetchall()]
    return jsonify({'history': list(reversed(history))})

@app.route('/api/generate-schedule', methods=['POST'])
@require_user
def generate_schedule(user_id):
    data = request.get_json()
    workflow = sanitize(data.get('workflow', ''), 5000)
    if not workflow:
        return jsonify({'error': 'Workflow required'}), 400
    
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute('INSERT INTO workflows (user_id, workflow_text) VALUES (?, ?)',
                      (user_id, workflow))
        workflow_id = cursor.lastrowid
    
    schedule_data = None
    if config.AI_ENABLED:
        schedule_data = get_ai_schedule(workflow)
    
    if not schedule_data:
        schedule_data = fallback_schedule(workflow)
    
    week_start = datetime.now().date() - timedelta(days=datetime.now().weekday())
    
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute('INSERT INTO schedules (user_id, week_start) VALUES (?, ?)',
                      (user_id, week_start))
        schedule_id = cursor.lastrowid
        
        for block in schedule_data.get('study_blocks', []):
            cursor.execute('''INSERT INTO study_blocks 
                (schedule_id, day_of_week, start_time, end_time, subject, topic, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (schedule_id, block['day'], block['start_time'], block['end_time'],
                 block['subject'], block.get('topic', ''), block.get('priority', 'medium')))
        
        cursor.execute('UPDATE workflows SET generated_schedule_id = ? WHERE id = ?',
                      (schedule_id, workflow_id))
    
    return jsonify({'success': True, 'schedule_id': schedule_id, 'schedule_data': schedule_data})

@app.route('/api/schedule', methods=['GET'])
@require_user
def get_schedule(user_id):
    week_start = request.args.get('week_start')
    if not week_start:
        week_start = datetime.now().date() - timedelta(days=datetime.now().weekday())
    
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute('SELECT id FROM schedules WHERE user_id = ? AND week_start = ?',
                      (user_id, week_start))
        schedule = cursor.fetchone()
        
        if not schedule:
            return jsonify({'schedule': None, 'blocks': []})
        
        cursor.execute('SELECT * FROM study_blocks WHERE schedule_id = ? ORDER BY day_of_week, start_time',
                      (schedule['id'],))
        blocks = [dict(row) for row in cursor.fetchall()]
    
    return jsonify({'schedule_id': schedule['id'], 'week_start': str(week_start), 'blocks': blocks})

@app.route('/api/goals', methods=['GET'])
@require_user
def get_goals(user_id):
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute('SELECT * FROM goals WHERE user_id = ? ORDER BY created_at', (user_id,))
        goals = [dict(row) for row in cursor.fetchall()]
    
    goal_map = {g['id']: g for g in goals}
    for g in goals:
        g['children'] = []
    
    root_goals = []
    for g in goals:
        if g['parent_id'] and g['parent_id'] in goal_map:
            goal_map[g['parent_id']]['children'].append(g)
        elif not g['parent_id']:
            root_goals.append(g)
    
    return jsonify({'goals': root_goals})

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'ai_enabled': config.AI_ENABLED,
        'ai_provider': config.AI_PROVIDER or 'fallback',
        'timestamp': datetime.now().isoformat()
    })

# ================================
# RUN
# ================================

if __name__ == '__main__':
    print("=" * 60)
    print("FocusFlow-AI Backend - FREE AI Edition")
    print("=" * 60)
    if config.AI_ENABLED:
        print(f"✓ AI Provider: {config.AI_PROVIDER.upper()}")
        print(f"✓ Model: {config.AI_MODEL}")
        print(f"✓ Cost: $0.00 (FREE)")
    else:
        print("✓ AI Provider: Fallback (no API needed)")
        print("✓ Cost: $0.00")
    print(f"✓ Server: http://localhost:{config.PORT}")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=config.PORT, threaded=True)
