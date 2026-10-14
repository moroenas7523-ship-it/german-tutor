import os
import json
import ollama
from groq import Groq
from datetime import datetime

# ============ الإعدادات ============
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY.startswith("gsk-") else None

PROGRESS_FILE = "german_progress.json"

# ============ تتبع التقدم ============
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "level": "A1",
        "lesson": 1,
        "vocabulary_learned": [],
        "exercises_completed": 0,
        "correct_answers": 0,
        "wrong_answers": 0,
        "started": datetime.now().strftime("%Y-%m-%d")
    }

def save_progress(progress):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

# ============ توليد الدروس ============
def generate_lesson(level, lesson_num, topic_hint=""):
    """يولّد درساً كاملاً"""
    prompt = f"""You are a friendly German language teacher for absolute beginners (Arabic speakers).

Create a complete lesson for LEVEL {level}, LESSON {lesson_num}.
{f"Topic: {topic_hint}" if topic_hint else ""}

Structure the lesson in Arabic with German content:

## الدرس {lesson_num}: [عنوان الدرس]

### 1. المفردات الجديدة (10 كلمات)
For each word:
- German word | Pronunciation in Arabic letters | Arabic meaning
- Example sentence (German + Arabic translation)

### 2. القاعدة الأساسية
Explain one grammar rule in simple Arabic with examples.

### 3. تمارين تفاعلية
Provide 5 exercises:
- Fill in the blank
- Multiple choice
- Translation (German ↔ Arabic)

### 4. محادثة قصيرة
A short dialogue (4-6 lines) in German with Arabic translation.

### 5. نصائح للحفظ
3 practical tips.

Keep it simple, encouraging, and progressive. Use lots of examples."""
    
    try:
        if client:
            r = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": prompt}]
            )
            return r.choices[0].message.content
        else:
            r = ollama.chat(model="llama3.2:1b", messages=[{"role": "user", "content": prompt}])
            return r["message"]["content"]
    except Exception as e:
        return f"Error: {e}"

# ============ تصحيح الإجابات ============
def check_answer(question, user_answer, correct_hint=""):
    """يصحح إجابة المستخدم مع شرح"""
    prompt = f"""You are a German teacher. Evaluate this answer:

Question: {question}
Student's answer: {user_answer}
{f"Hint: {correct_hint}" if correct_hint else ""}

Provide feedback in Arabic:
1. Is the answer correct? (نعم/لا/قريب)
2. Explanation of the correction
3. The correct answer
4. An encouraging note

Be supportive and constructive."""
    
    try:
        r = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}]
        )
        return r.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# ============ محادثة مع الوكيل ============
def chat_with_tutor(user_input):
    """محادثة حرة مع المدرس"""
    prompt = f"""You are a patient German teacher for Arabic speakers. 
Respond to the student's message in a helpful way.
- If they ask a question → answer it clearly.
- If they write in German → gently correct errors.
- If they ask for practice → give them an exercise.
- Use Arabic for explanations and German for examples.

Student: {user_input}"""
    
    try:
        r = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}]
        )
        return r.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# ============ البرنامج الرئيسي ============
def main():
    progress = load_progress()
    
    print("\n" + "="*65)
    print("🇩🇪 German Tutor Agent - معلم الألمانية")
    print("="*65)
    print(f"📊 Level: {progress['level']}  |  Lesson: {progress['lesson']}")
    print(f"📚 Words learned: {len(progress['vocabulary_learned'])}")
    print(f"✅ Correct: {progress['correct_answers']}  ❌ Wrong: {progress['wrong_answers']}")
    print("="*65)
    print("\nCommands:")
    print("  lesson       → درس جديد")
    print("  next         → الدرس التالي")
    print("  vocab        → مفرداتي")
    print("  quiz         → اختبار سريع")
    print("  ask <q>      → اسأل سؤالاً")
    print("  chat <msg>   → محادثة حرة")
    print("  level A1/A2/B1 → تغيير المستوى")
    print("  reset        → إعادة تعيين")
    print("  exit         → خروج")
    print("="*65 + "\n")
    
    while True:
        try:
            cmd = input("You: ").strip()
        except:
            break
        
        if not cmd:
            continue
        if cmd.lower() == "exit":
            save_progress(progress)
            print("💾 Progress saved. Tschüss! 👋")
            break
        
        if cmd == "lesson":
            print(f"\n📖 Generating lesson {progress['lesson']}...\n")
            lesson = generate_lesson(progress['level'], progress['lesson'])
            print(lesson)
            print("\n" + "="*65 + "\n")
        
        elif cmd == "next":
            progress['lesson'] += 1
            save_progress(progress)
            print(f"\n📖 Lesson {progress['lesson']} (Level {progress['level']})\n")
            lesson = generate_lesson(progress['level'], progress['lesson'])
            print(lesson)
            print("\n" + "="*65 + "\n")
        
        elif cmd == "vocab":
            if progress['vocabulary_learned']:
                print(f"\n📚 My Vocabulary ({len(progress['vocabulary_learned'])} words):\n")
                for w in progress['vocabulary_learned']:
                    print(f"  • {w}")
                print()
            else:
                print("\n📚 لا توجد مفردات محفوظة بعد. ابدأ بدرس!\n")
        
        elif cmd == "quiz":
            print("\n🎯 Quick Quiz...\n")
            quiz = chat_with_tutor("Give me 3 quick quiz questions for my current level. Ask one at a time.")
            print(quiz)
            print()
        
        elif cmd.startswith("ask "):
            question = cmd[4:]
            print("\n🤔 Thinking...\n")
            answer = chat_with_tutor(question)
            print(answer)
            print()
        
        elif cmd.startswith("chat "):
            msg = cmd[5:]
            print()
            answer = chat_with_tutor(msg)
            print(answer)
            print()
        
        elif cmd.startswith("level "):
            new_level = cmd[6:].strip().upper()
            if new_level in ["A1", "A2", "B1"]:
                progress['level'] = new_level
                progress['lesson'] = 1
                save_progress(progress)
                print(f"\n✓ Level changed to {new_level}. Starting from lesson 1.\n")
            else:
                print("\n⚠️ Use: level A1 / A2 / B1\n")
        
        elif cmd == "reset":
            confirm = input("Are you sure? (yes/no): ")
            if confirm.lower() == "yes":
                progress = {
                    "level": "A1",
                    "lesson": 1,
                    "vocabulary_learned": [],
                    "exercises_completed": 0,
                    "correct_answers": 0,
                    "wrong_answers": 0,
                    "started": datetime.now().strftime("%Y-%m-%d")
                }
                save_progress(progress)
                print("\n✓ Progress reset.\n")
        
        else:
            # معاملة أي شيء آخر كسؤال
            print()
            answer = chat_with_tutor(cmd)
            print(answer)
            print()

if __name__ == "__main__":
    main()
