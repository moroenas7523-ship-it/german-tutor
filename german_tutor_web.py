import os
import json
import io
from flask import Flask, request, jsonify, Response
from groq import Groq
from gtts import gTTS
import markdown

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY.startswith("gsk-") else None

PROGRESS_FILE = "german_progress.json"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"level": "A1", "lesson": 1}

def save_progress(p):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(p, f, ensure_ascii=False, indent=2)

def ask_ai(prompt):
    if not client:
        return "No AI client"
    try:
        r = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}]
        )
        return r.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

HTML = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<title>معلم الألمانية</title>
<style>
body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #1a1a2e, #16213e); min-height: 100vh; color: #eee; padding: 20px; margin: 0; }
.container { max-width: 900px; margin: 0 auto; }
header { text-align: center; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 15px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1); }
h1 { color: #ffcc00; font-size: 28px; margin: 0 0 8px 0; }
.subtitle { color: #aaa; font-size: 14px; }
.stats { display: flex; gap: 15px; justify-content: center; margin-top: 15px; flex-wrap: wrap; }
.stat { background: rgba(255,204,0,0.1); padding: 8px 15px; border-radius: 20px; font-size: 13px; border: 1px solid rgba(255,204,0,0.3); }
.stat strong { color: #ffcc00; }
.buttons { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-bottom: 20px; }
button { padding: 15px; border: none; border-radius: 12px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; font-size: 15px; cursor: pointer; font-weight: bold; transition: transform 0.2s; }
button:hover { transform: translateY(-2px); }
button.primary { background: linear-gradient(135deg, #ffcc00, #ff9900); color: #000; }
button.speak { padding: 3px 8px; margin-right: 5px; font-size: 13px; background: rgba(255,204,0,0.4); border-radius: 6px; cursor: pointer; border: none; color: #fff; }
#content { background: rgba(255,255,255,0.05); border-radius: 15px; padding: 25px; min-height: 400px; border: 1px solid rgba(255,255,255,0.1); line-height: 1.9; font-size: 15px; overflow-y: auto; max-height: 600px; }
#content h2 { color: #ffcc00; margin: 20px 0 10px 0; border-right: 4px solid #ffcc00; padding-right: 10px; }
#content h3 { color: #88ccff; margin: 15px 0 8px 0; }
#content strong { color: #ffcc00; }
#content table { width: 100%; border-collapse: collapse; margin: 15px 0; }
#content th { background: rgba(255,204,0,0.2); padding: 10px; text-align: right; }
#content td { border: 1px solid rgba(255,255,255,0.1); padding: 8px; }
#content code { background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px; color: #88ff88; }
.input-area { display: flex; gap: 10px; margin-top: 20px; }
input { flex: 1; padding: 15px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.2); background: rgba(255,255,255,0.05); color: #eee; font-size: 15px; }
.loader { display: none; text-align: center; padding: 20px; color: #ffcc00; }
.loader.show { display: block; }
</style>
</head>
<body>
<div class="container">
    <header>
        <h1>معلم الألمانية الذكي</h1>
        <div class="subtitle">تعلم الألمانية من A1 إلى B1</div>
        <div class="stats">
            <div class="stat">المستوى: <strong id="level">A1</strong></div>
            <div class="stat">الدرس: <strong id="lesson">1</strong></div>
        </div>
    </header>
    <div class="buttons">
        <button class="primary" onclick="doAction('lesson')">درس جديد</button>
        <button onclick="doAction('prev')">⬅️ الدرس السابق</button>
        <button onclick="doAction('next')">➡️ الدرس التالي</button>
        <button onclick="doAction('quiz')">اختبار سريع</button>
        <button onclick="doAction('vocab')">مفرداتي</button>
        <button onclick="doAction('tips')">نصائح</button>
    </div>
    <div id="content">مرحباً! اضغط "درس جديد" لتبدأ.</div>
    <div class="loader" id="loader">جاري التحضير...</div>
    <div class="input-area">
        <input id="msg" placeholder="اسأل أي سؤال..." onkeypress="if(event.key==='Enter')sendMsg()">
        <button onclick="sendMsg()">إرسال</button>
    </div>
</div>
<script>
async function speak(text) {
    try {
        const r = await fetch('/tts', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({text: text})
        });
        if (!r.ok) throw new Error('TTS failed');
        const blob = await r.blob();
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.play();
    } catch(e) {
        alert('خطأ في الصوت: ' + e);
    }
}
function addSpeakButtons() {
    const content = document.getElementById('content');
    content.querySelectorAll('td').forEach(td => {
        const text = td.textContent.trim();
        if (text && text.length > 2 && text.length < 40 && /^[a-zA-ZäöüßÄÖÜ\s\-]+$/.test(text)) {
            if (!td.querySelector('button.speak')) {
                const btn = document.createElement('button');
                btn.className = 'speak';
                btn.textContent = '🔊';
                btn.onclick = () => speak(text);
                td.insertBefore(btn, td.firstChild);
            }
        }
    });
}
async function updateStats() {
    const r = await fetch('/stats');
    const d = await r.json();
    document.getElementById('level').textContent = d.level;
    document.getElementById('lesson').textContent = d.lesson;
}
async function doAction(action) {
    document.getElementById('loader').classList.add('show');
    const r = await fetch('/action', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({action: action})
    });
    const d = await r.json();
    document.getElementById('content').innerHTML = d.content;
    document.getElementById('loader').classList.remove('show');
    await updateStats();
    setTimeout(addSpeakButtons, 300);
}
async function sendMsg() {
    const msg = document.getElementById('msg').value.trim();
    if (!msg) return;
    document.getElementById('msg').value = '';
    document.getElementById('content').innerHTML = '<strong>أنت:</strong> ' + msg + '<br><br>';
    document.getElementById('loader').classList.add('show');
    const r = await fetch('/ask', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: msg})
    });
    const d = await r.json();
    document.getElementById('content').innerHTML += '<strong>المعلم:</strong><br>' + d.content;
    document.getElementById('loader').classList.remove('show');
    setTimeout(addSpeakButtons, 300);
}
updateStats();
</script>
</body>
</html>"""

def md_to_html(text):
    return markdown.markdown(text, extensions=['tables'])

@app.route('/')
def home():
    return HTML

@app.route('/tts', methods=['POST'])
def tts():
    data = request.json
    text = data.get('text', '')
    if not text:
        return Response('No text', status=400)
    try:
        tts = gTTS(text=text, lang='de', slow=False)
        audio = io.BytesIO()
        tts.write_to_fp(audio)
        audio.seek(0)
        return Response(audio.read(), mimetype='audio/mpeg')
    except Exception as e:
        return Response(f'Error: {e}', status=500)

@app.route('/stats')
def stats():
    p = load_progress()
    return jsonify({"level": p.get("level", "A1"), "lesson": p.get("lesson", 1)})

@app.route('/action', methods=['POST'])
def action():
    data = request.json
    act = data.get('action')
    p = load_progress()
    
    if act == 'lesson':
        prompt = f"You are a German teacher for Arabic beginners. Create a complete lesson for LEVEL {p['level']}, LESSON {p['lesson']}. Write in Arabic with German examples. Include: 1) Lesson goals, 2) 10 vocabulary words in a table (German | Pronunciation | Arabic), 3) One grammar rule, 4) 5 exercises, 5) Short dialogue, 6) 3 tips. Use markdown."
        content = ask_ai(prompt)
        p['lesson'] += 1
        save_progress(p)
        return jsonify({"content": md_to_html(content)})
    
    elif act == 'next':
        p['lesson'] += 1
        save_progress(p)
        prompt = f"Create lesson {p['lesson']} for level {p['level']} in Arabic with German examples. Include vocab table, grammar, exercises, dialogue."
        content = ask_ai(prompt)
        return jsonify({"content": md_to_html(content)})
    
    elif act == 'prev':
        if p['lesson'] > 1:
            p['lesson'] -= 1
        save_progress(p)
        prompt = f"Create lesson {p['lesson']} for level {p['level']} in Arabic with German examples. Include vocab table, grammar, exercises, dialogue."
        content = ask_ai(prompt)
        return jsonify({"content": md_to_html(content)})
    
    elif act == 'quiz':
        prompt = f"Create a 5-question German quiz for level {p['level']} with Arabic explanations. Include answers at the end."
        content = ask_ai(prompt)
        return jsonify({"content": md_to_html(content)})
    
    elif act == 'vocab':
        prompt = f"Create a vocabulary review for German level {p['level']}. Table with 20 words: German | Pronunciation | Arabic. Organized by theme."
        content = ask_ai(prompt)
        return jsonify({"content": md_to_html(content)})
    
    elif act == 'tips':
        prompt = "Give 10 golden tips for learning German as an Arabic speaker. In Arabic, practical and motivating."
        content = ask_ai(prompt)
        return jsonify({"content": md_to_html(content)})
    
    return jsonify({"content": "Unknown"})

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    msg = data.get('message', '')
    p = load_progress()
    prompt = f"You are a patient German teacher for an Arabic speaker at level {p['level']}. Answer in Arabic with German examples. Student asks: {msg}"
    content = ask_ai(prompt)
    return jsonify({"content": md_to_html(content)})

if __name__ == '__main__':
    print("\nOpen in browser: http://localhost:5001\n")
    app.run(host='0.0.0.0', port=5001, debug=False)
