import psycopg2
import psycopg2.extras
import os
from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)

@contextmanager
def db():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                language TEXT DEFAULT 'uz',
                is_subscribed BOOLEAN DEFAULT FALSE,
                subscription_price INTEGER DEFAULT 0,
                added_by BIGINT,
                added_by_username TEXT,
                joined_at TIMESTAMP DEFAULT NOW(),
                last_active TIMESTAMP DEFAULT NOW(),
                total_quizzes_taken INTEGER DEFAULT 0,
                total_correct INTEGER DEFAULT 0,
                total_wrong INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS admins (
                admin_id BIGINT PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                added_by BIGINT,
                added_at TIMESTAMP DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS admin_logs (
                id SERIAL PRIMARY KEY,
                admin_id BIGINT,
                admin_username TEXT,
                action TEXT,
                target_user_id BIGINT,
                target_username TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS quizzes (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                quiz_name TEXT,
                total_questions INTEGER,
                correct_answers INTEGER DEFAULT 0,
                wrong_answers INTEGER DEFAULT 0,
                started_at TIMESTAMP DEFAULT NOW(),
                finished_at TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            );
            CREATE TABLE IF NOT EXISTS quiz_questions (
                id SERIAL PRIMARY KEY,
                quiz_session_id INTEGER REFERENCES quizzes(id),
                question_number INTEGER,
                question_text TEXT,
                option_a TEXT,
                option_b TEXT,
                option_c TEXT,
                option_d TEXT,
                correct_answer TEXT,
                user_answer TEXT,
                is_correct BOOLEAN,
                answered_at TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT NOW()
            );
            INSERT INTO bot_settings (key, value) VALUES ('subscription_price', '10000')
            ON CONFLICT (key) DO NOTHING;
        """)

# ===== USER =====
def get_user(user_id):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        return cur.fetchone()

def add_user(user_id, username, full_name, language='uz'):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (user_id, username, full_name, language)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                username = EXCLUDED.username,
                full_name = EXCLUDED.full_name,
                last_active = NOW()
        """, (user_id, username, full_name, language))

def update_user_language(user_id, language):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET language = %s WHERE user_id = %s", (language, user_id))

def subscribe_user(user_id, added_by, added_by_username, price=None):
    if price is None:
        price = int(get_setting('subscription_price') or 10000)
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE users SET is_subscribed = TRUE, subscription_price = %s,
            added_by = %s, added_by_username = %s WHERE user_id = %s
        """, (price, added_by, added_by_username, user_id))

def unsubscribe_user(user_id):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_subscribed = FALSE WHERE user_id = %s", (user_id,))

def get_all_users(limit=100, offset=0):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users ORDER BY joined_at DESC LIMIT %s OFFSET %s", (limit, offset))
        return cur.fetchall()

def get_subscribed_users():
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE is_subscribed = TRUE ORDER BY joined_at DESC")
        return cur.fetchall()

def get_users_count():
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_subscribed = TRUE) as subscribed,
                COUNT(*) FILTER (WHERE DATE(joined_at) = CURRENT_DATE) as today
            FROM users
        """)
        return cur.fetchone()

def search_user(query):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM users
            WHERE user_id::text = %s OR username ILIKE %s OR full_name ILIKE %s
            LIMIT 10
        """, (query, f"%{query}%", f"%{query}%"))
        return cur.fetchall()

# ===== ADMIN =====
def is_admin(user_id):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM admins WHERE admin_id = %s", (user_id,))
        return cur.fetchone() is not None

def add_admin(admin_id, username, full_name, added_by):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO admins (admin_id, username, full_name, added_by)
            VALUES (%s, %s, %s, %s) ON CONFLICT (admin_id) DO UPDATE SET username = EXCLUDED.username
        """, (admin_id, username, full_name, added_by))

def remove_admin(admin_id):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM admins WHERE admin_id = %s", (admin_id,))

def get_all_admins():
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM admins ORDER BY added_at DESC")
        return cur.fetchall()

def log_admin_action(admin_id, admin_username, action, target_user_id=None, target_username=None, details=None):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO admin_logs (admin_id, admin_username, action, target_user_id, target_username, details)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (admin_id, admin_username, action, target_user_id, target_username, details))

def get_admin_logs(admin_id=None, limit=20):
    with db() as conn:
        cur = conn.cursor()
        if admin_id:
            cur.execute("SELECT * FROM admin_logs WHERE admin_id = %s ORDER BY created_at DESC LIMIT %s", (admin_id, limit))
        else:
            cur.execute("SELECT * FROM admin_logs ORDER BY created_at DESC LIMIT %s", (limit,))
        return cur.fetchall()

def get_admin_stats(admin_id):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) as total_actions,
                COUNT(*) FILTER (WHERE action = 'subscribe') as subscribed_count,
                COUNT(*) FILTER (WHERE action = 'unsubscribe') as unsubscribed_count,
                COUNT(*) FILTER (WHERE action = 'add_admin') as added_admins
            FROM admin_logs WHERE admin_id = %s
        """, (admin_id,))
        return cur.fetchone()

# ===== QUIZ =====
def create_quiz_session(user_id, quiz_name, total_questions):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO quizzes (user_id, quiz_name, total_questions)
            VALUES (%s, %s, %s) RETURNING id
        """, (user_id, quiz_name, total_questions))
        return cur.fetchone()['id']

def get_active_quiz(user_id):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM quizzes WHERE user_id = %s AND is_active = TRUE
            ORDER BY started_at DESC LIMIT 1
        """, (user_id,))
        return cur.fetchone()

def save_question(session_id, q_num, question, a, b, c, d, correct):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO quiz_questions
            (quiz_session_id, question_number, question_text, option_a, option_b, option_c, option_d, correct_answer)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (session_id, q_num, question, a, b, c, d, correct))

def answer_question(session_id, q_num, user_answer):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT correct_answer FROM quiz_questions
            WHERE quiz_session_id = %s AND question_number = %s
        """, (session_id, q_num))
        q = cur.fetchone()
        if not q:
            return None
        is_correct = user_answer.upper() == q['correct_answer'].upper()
        cur.execute("""
            UPDATE quiz_questions SET user_answer = %s, is_correct = %s, answered_at = NOW()
            WHERE quiz_session_id = %s AND question_number = %s
        """, (user_answer, is_correct, session_id, q_num))
        if is_correct:
            cur.execute("UPDATE quizzes SET correct_answers = correct_answers + 1 WHERE id = %s", (session_id,))
        else:
            cur.execute("UPDATE quizzes SET wrong_answers = wrong_answers + 1 WHERE id = %s", (session_id,))
        return is_correct

def finish_quiz(session_id):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM quizzes WHERE id = %s", (session_id,))
        quiz = cur.fetchone()
        cur.execute("UPDATE quizzes SET is_active = FALSE, finished_at = NOW() WHERE id = %s", (session_id,))
        if quiz:
            cur.execute("""
                UPDATE users SET
                    total_quizzes_taken = total_quizzes_taken + 1,
                    total_correct = total_correct + %s,
                    total_wrong = total_wrong + %s
                WHERE user_id = %s
            """, (quiz['correct_answers'], quiz['wrong_answers'], quiz['user_id']))
        return quiz

# ===== SETTINGS =====
def get_setting(key):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT value FROM bot_settings WHERE key = %s", (key,))
        row = cur.fetchone()
        return row['value'] if row else None

def set_setting(key, value):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO bot_settings (key, value, updated_at) VALUES (%s, %s, NOW())
            ON CONFLICT (key) DO UPDATE SET value = %s, updated_at = NOW()
        """, (key, value, value))
