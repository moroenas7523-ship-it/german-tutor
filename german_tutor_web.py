import os
import json
import io
from flask import Flask, request, jsonify, Response, render_template_string
from groq import Groq
from gtts import gTTS
import markdown

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY.startswith("gsk_") else None

# ============ Offizielles Nicos Weg A1 Curriculum (12 Kapitel) ============
CURRICULUM = {
    "A1": {
        "K1": {"title": "Hallo!", "topic": "Begrüßung und Vorstellung", "grammar": "Personalpronomen: ich, du"},
        "K2": {"title": "Kein Problem!", "topic": "Erste Wörter und Bitten", "grammar": "Formell vs. informell"},
        "K3": {"title": "Tschüss!", "topic": "Verabschiedung", "grammar": "Verabschiedungsformeln"},
        "K4": {"title": "Von A bis Z", "topic": "Alphabet und Buchstabieren", "grammar": "Alphabet"},
        "K5": {"title": "Zahlen von 1 bis 100", "topic": "Zahlen und Nummern", "grammar": "Zahlen 1-100"},
        "K6": {"title": "Eine Pizza, bitte!", "topic": "Essen und Trinken bestellen", "grammar": "Artikel: der/die/das"},
        "K7": {"title": "Was machst du hier?", "topic": "Alltagsaktivitäten", "grammar": "Präsens: regelmäßige Verben"},
        "K8": {"title": "Wo wohnst du?", "topic": "Wohnen und Adresse", "grammar": "Präpositionen: in, an, bei"},
        "K9": {"title": "Wie spät ist es?", "topic": "Uhrzeit und Zeitangaben", "grammar": "Trennbare Verben"},
        "K10": {"title": "Wo ist der Bahnhof?", "topic": "Wege und Orientierung", "grammar": "Imperativ"},
        "K11": {"title": "Mein Beruf", "topic": "Arbeit und Berufe", "grammar": "Modalverben: können, müssen"},
        "K12": {"title": "Emmas Tag", "topic": "Tagesablauf", "grammar": "Trennbare Verben (2)"}
    }
}

PROGRESS_FILE = "german_progress.json"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"level": "A1", "lektion": "K1"}

def save_progress(p):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(p, f, ensure_ascii=False, indent=2)

def ask_ai(prompt, system_prompt):
    if not client:
        return "No AI client"
    try:
        r = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return r.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

def text_to_speech(text, lang='de'):
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return mp3_fp
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

# ============ HTML ============
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<title>🇩🇪 Deutsch-Tutor (Nicos Weg A1)</title>
<style>
    * { box-sizing: border-box; }
    body { font-family: 'Segoe UI', Tahoma, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 0; padding: 20px; min-height: 100vh; }
    .container { max-width: 950px; margin: auto; background: #ffffff; padding: 30px; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
    h1 { text-align: center; color: #1a73e8; margin: 0 0 5px; font-size: 28px; }
    .subtitle { text-align: center; color: #666; margin-bottom: 25px; font-size: 14px; }
    .info-bar { display: flex; justify-content: space-around; background: linear-gradient(90deg, #e8f0fe, #d2e3fc); padding: 15px; border-radius: 12px; margin-bottom: 20px; font-weight: 600; color: #1a73e8; }
    .controls { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; margin-bottom: 25px; }
    .controls select { padding: 12px; border: 2px solid #1a73e8; border-radius: 10px; font-size: 15px; background: white; color: #1a73e8; font-weight: 600; cursor: pointer; }
    button { background: linear-gradient(135deg, #1a73e8, #1557b0); color: white; border: none; padding: 12px 22px; border-radius: 10px; cursor: pointer; font-size: 15px; font-weight: 600; transition: transform 0.2s, box-shadow 0.2s; }
    button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(26,115,232,0.4); }
    .btn-test { background: linear-gradient(135deg, #f09300, #e37400); }
    .btn-vocab { background: linear-gradient(135deg, #34a853, #2c8e47); }
    .content { background: #f8f9fa; padding: 25px; border-radius: 15px; min-height: 300px; line-height: 2; font-size: 16px; color: #333; border-right: 5px solid #1a73e8; }
    .content h2 { color: #1a73e8; border-bottom: 2px solid #e8f0fe; padding-bottom: 8px; margin-top: 25px; }
    .content h3 { color: #34a853; }
    .content table { width: 100%; border-collapse: collapse; margin: 15px 0; }
    .content th { background: #1a73e8; color: white; padding: 10px; }
    .content td { border: 1px solid #ddd; padding: 10px; text-align: center; }
    .content tr:nth-child(even) { background: #f0f4ff; }
    .speak-btn { background: #4285f4; border: none; border-radius: 50%; width: 35px; height: 35px; cursor: pointer; font-size: 16px; margin: 0 5px; padding: 0; }
    .loading { text-align: center; color: #1a73e8; font-size: 18px; padding: 40px; }
    .loading::after { content: ''; display: inline-block; width: 20px; height: 20px; border: 3px solid #e8f0fe; border-top-color: #1a73e8; border-radius: 50%; animation: spin 1s linear infinite; margin-right: 10px; vertical-align: middle; }
    @keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
<div class="container">
    <h1>🇩🇪 Deutsch-Tutor</h1>
    <p class="subtitle">Basierend auf „Nicos Weg" A1 – Deutsche Welle</p>
    <div class="info-bar">
        <span>📊 Niveau: <span id="level">A1</span></span>
        <span>📖 Lektion: <span id="lektion">K1</span></span>
    </div>
    <div class="controls">
        <select id="levelSelect" onchange="updateLevel()">
            <option value="A1">A1 - Anfänger</option>
        </select>
        <select id="lektionSelect" onchange="updateLektion()"></select>
        <button onclick="loadLesson()">📖 Lektion</button>
        <button class="btn-test" onclick="startTest()">📝 Test</button>
        <button class="btn-vocab" onclick="showVocab()">📚 Vokabeln</button>
    </div>
    <div class="content" id="content">
        <div class="loading">Wähle eine Lektion und klicke auf "Lektion"</div>
    </div>
</div>

<script>
const CURRICULUM = {{ curriculum | safe }};
let currentLevel = "A1";
let currentLektion = "K1";

function updateLektionOptions() {
    const sel = document.getElementById('lektionSelect');
    sel.innerHTML = '';
    const lessons = Object.keys(CURRICULUM[currentLevel]);
    lessons.forEach(l => {
        const opt = document.createElement('option');
        opt.value = l;
        opt.text = l + ': ' + CURRICULUM[currentLevel][l].title;
        sel.appendChild(opt);
    });
    currentLektion = lessons[0];
}

function updateLevel() {
    currentLevel = document.getElementById('levelSelect').value;
    updateLektionOptions();
    document.getElementById('level').innerText = currentLevel;
}

function updateLektion() {
    currentLektion = document.getElementById('lektionSelect').value;
    document.getElementById('lektion').innerText = currentLektion;
}

function setLoading(text) {
    document.getElementById('content').innerHTML = '<div class="loading">' + text + '</div>';
}

async function loadLesson() {
    setLoading('Lektion wird geladen...');
    const res = await fetch('/lesson', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({level: currentLevel, lektion: currentLektion})
    });
    const data = await res.json();
    document.getElementById('content').innerHTML = data.html;
    attachSpeakButtons();
}

async function startTest() {
    setLoading('Test wird erstellt...');
    const res = await fetch('/test', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({level: currentLevel, lektion: currentLektion})
    });
    const data = await res.json();
    document.getElementById('content').innerHTML = data.html;
}

async function showVocab() {
    setLoading('Vokabeln werden geladen...');
    const res = await fetch('/vocab', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({level: currentLevel, lektion: currentLektion})
    });
    const data = await res.json();
    document.getElementById('content').innerHTML = data.html;
    attachSpeakButtons();
}

function attachSpeakButtons() {
    document.querySelectorAll('.speak-btn').forEach(btn => {
        btn.onclick = function() {
            const word = this.getAttribute('data-word');
            speakWord(word);
        };
    });
}

async function speakWord(word) {
    try {
        const res = await fetch('/speak', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({text: word})
        });
        const blob = await res.blob();
        const audio = new Audio(URL.createObjectURL(blob));
        audio.play();
    } catch (e) { console.error('Audio error:', e); }
}

setTimeout(() => {
    const observer = new MutationObserver(() => attachSpeakButtons());
    observer.observe(document.getElementById('content'), { childList: true, subtree: true });
}, 1000);

updateLektionOptions();
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, curriculum=json.dumps(CURRICULUM, ensure_ascii=False))

@app.route('/lesson', methods=['POST'])
def lesson():
    data = request.json
    level = data.get('level', 'A1')
    lektion = data.get('lektion', 'K1')
    
    if level not in CURRICULUM or lektion not in CURRICULUM[level]:
        return jsonify({"html": "<p>Lektion nicht gefunden.</p>"})
    
    lesson_info = CURRICULUM[level][lektion]
    
    system_prompt = """You are a German teacher for Arabic speakers, using the official "Nicos Weg" A1 curriculum from Deutsche Welle.
RULES:
1. Main content in GERMAN. Arabic translation below each German word.
2. Use emojis for vocabulary.
3. Create a COMPLETE lesson with: Lernziele, Vokabeln (table), Dialog (with audio), Grammatik, Übungen.
4. Format as clean HTML."""
    
    prompt = f"""Erstelle eine vollständige Deutschlektion "{lesson_info['title']}" zum Thema "{lesson_info['topic']}" (Grammatik: {lesson_info['grammar']}) für Niveau A1.

Struktur:
## 🎯 Lernziele
(3-4 Ziele auf Deutsch mit arabischer Übersetzung)

## 📚 Vokabeln
Tabelle mit 12 Wörtern: | Deutsch | Artikel | Arabisch | Emoji |

## 💬 Dialog
Ein kurzer Dialog (8 Zeilen) auf Deutsch, mit arabischer Übersetzung unter jeder Zeile.

## 📖 Grammatik: {lesson_info['grammar']}
Eine einfache Regel auf Deutsch, mit arabischer Erklärung.

## ✏️ Übungen
2 kurze Übungen.

Gib nur den HTML-Inhalt zurück (kein <html> Tag). Verwende <h2>, <h3>, <table>, <p>, <ul>."""
    
    content = ask_ai(prompt, system_prompt)
    html_content = markdown.markdown(content, extensions=['tables', 'fenced_code'])
    return jsonify({"html": html_content})

@app.route('/test', methods=['POST'])
def test():
    data = request.json
    level = data.get('level', 'A1')
    lektion = data.get('lektion', 'K1')
    lesson_info = CURRICULUM[level][lektion]
    
    system_prompt = """You are a German teacher creating multiple-choice tests for Arabic speakers.
RULES:
1. Questions in GERMAN. Arabic translation below.
2. 4 options (A, B, C, D) in German.
3. Mark correct answer.
4. Return as clean HTML."""
    
    prompt = f"""Erstelle einen Multiple-Choice-Test (5 Fragen) zum Thema "{lesson_info['topic']}" für Niveau A1.

Format:
<div class="question">
<h3>Frage 1: [السؤال بالألماني]</h3>
<p><em>[الترجمة العربية]</em></p>
<ul><li>A) ...</li><li>B) ...</li><li>C) ...</li><li>D) ...</li></ul>
<p><strong>✅ Richtige Antwort: X</strong></p>
</div>

Gib nur sauberes HTML zurück."""
    
    content = ask_ai(prompt, system_prompt)
    return jsonify({"html": content})

@app.route('/vocab', methods=['POST'])
def vocab():
    data = request.json
    level = data.get('level', 'A1')
    lektion = data.get('lektion', 'K1')
    lesson_info = CURRICULUM[level][lektion]
    
    system_prompt = """Create a vocabulary list in HTML for German learners.
RULES:
1. German words with articles
2. Arabic translation
3. Emoji for each word
4. Add a speaker button: <button class="speak-btn" data-word="WORD">🔊</button>
5. Use a clean table"""
    
    prompt = f"""Erstelle eine Vokabelliste (15 Wörter) zum Thema "{lesson_info['topic']}" für Niveau A1.

Format:
<table>
<tr><th>🔊</th><th>Deutsch</th><th>Arabisch</th><th>Emoji</th></tr>
<tr><td><button class="speak-btn" data-word="Apfel">🔊</button></td><td>der Apfel</td><td>تفاحة</td><td>🍎</td></tr>
...
</table>

Gib nur die Tabelle zurück."""
    
    content = ask_ai(prompt, system_prompt)
    return jsonify({"html": content})

@app.route('/speak', methods=['POST'])
def speak():
    data = request.json
    text = data.get('text', '')
    if not text:
        return Response(status=400)
    audio = text_to_speech(text, 'de')
    if audio is None:
        return Response(status=500)
    return Response(audio.read(), mimetype='audio/mpeg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
