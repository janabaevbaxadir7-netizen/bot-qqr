import asyncpg
import os
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")

pool = None

async def init_db():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=20)
    await create_tables()

async def get_pool():
    return pool

async def create_tables():
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                language TEXT DEFAULT 'uz',
                is_subscribed BOOLEAN DEFAULT FALSE,
                subscription_expires TIMESTAMP,
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
                added_at TIMESTAMP DEFAULT NOW(),
                permissions JSONB DEFAULT '{"can_add_users": true, "can_remove_users": true, "can_view_users": true}'::jsonb
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

            INSERT INTO bot_settings (key, value) VALUES
                ('subscription_price', '10000'),
                ('subscription_note', ''),
                ('bot_active', 'true')
            ON CONFLICT (key) DO NOTHING;
        """)

# ==================== USER FUNCTIONS ====================

async def get_user(user_id: int):
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)

async def add_user(user_id: int, username: str, full_name: str, language: str = 'uz'):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, username, full_name, language)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id) DO UPDATE SET
                username = EXCLUDED.username,
                full_name = EXCLUDED.full_name,
                last_active = NOW()
        """, user_id, username, full_name, language)

async def update_user_language(user_id: int, language: str):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET language = $1 WHERE user_id = $2", language, user_id)

async def subscribe_user(user_id: int, added_by: int, added_by_username: str, price: int = None):
    if price is None:
        price = int(await get_setting('subscription_price') or 10000)
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE users SET
                is_subscribed = TRUE,
                subscription_expires = NULL,
                subscription_price = $2,
                added_by = $3,
                added_by_username = $4
            WHERE user_id = $1
        """, user_id, price, added_by, added_by_username)

async def unsubscribe_user(user_id: int):
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE users SET is_subscribed = FALSE WHERE user_id = $1
        """, user_id)

async def get_all_users(limit: int = 100, offset: int = 0):
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT u.*, 
                   CASE WHEN u.added_by_username IS NOT NULL 
                        THEN u.added_by_username ELSE 'Noma''lum' END as subscriber_by
            FROM users u
            ORDER BY u.joined_at DESC
            LIMIT $1 OFFSET $2
        """, limit, offset)

async def get_subscribed_users():
    async with pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM users WHERE is_subscribed = TRUE ORDER BY joined_at DESC")

async def get_users_count():
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_subscribed = TRUE) as subscribed,
                COUNT(*) FILTER (WHERE DATE(joined_at) = CURRENT_DATE) as today
            FROM users
        """)
        return row

async def search_user(query: str):
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT * FROM users 
            WHERE user_id::text = $1 OR username ILIKE $2 OR full_name ILIKE $2
            LIMIT 10
        """, query, f"%{query}%")

async def update_last_active(user_id: int):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET last_active = NOW() WHERE user_id = $1", user_id)

# ==================== ADMIN FUNCTIONS ====================

async def is_admin(user_id: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM admins WHERE admin_id = $1", user_id)
        return row is not None

async def add_admin(admin_id: int, username: str, full_name: str, added_by: int):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO admins (admin_id, username, full_name, added_by)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (admin_id) DO UPDATE SET username = EXCLUDED.username
        """, admin_id, username, full_name, added_by)

async def remove_admin(admin_id: int):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM admins WHERE admin_id = $1", admin_id)

async def get_all_admins():
    async with pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM admins ORDER BY added_at DESC")

async def log_admin_action(admin_id: int, admin_username: str, action: str, 
                            target_user_id: int = None, target_username: str = None, details: str = None):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO admin_logs (admin_id, admin_username, action, target_user_id, target_username, details)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, admin_id, admin_username, action, target_user_id, target_username, details)

async def get_admin_logs(admin_id: int = None, limit: int = 20):
    async with pool.acquire() as conn:
        if admin_id:
            return await conn.fetch("""
                SELECT * FROM admin_logs WHERE admin_id = $1 ORDER BY created_at DESC LIMIT $2
            """, admin_id, limit)
        return await conn.fetch("SELECT * FROM admin_logs ORDER BY created_at DESC LIMIT $1", limit)

async def get_admin_stats(admin_id: int):
    async with pool.acquire() as conn:
        return await conn.fetchrow("""
            SELECT
                COUNT(*) as total_actions,
                COUNT(*) FILTER (WHERE action = 'subscribe') as subscribed_count,
                COUNT(*) FILTER (WHERE action = 'unsubscribe') as unsubscribed_count,
                COUNT(*) FILTER (WHERE action = 'add_admin') as added_admins
            FROM admin_logs WHERE admin_id = $1
        """, admin_id)

# ==================== QUIZ FUNCTIONS ====================

async def create_quiz_session(user_id: int, quiz_name: str, total_questions: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO quizzes (user_id, quiz_name, total_questions)
            VALUES ($1, $2, $3) RETURNING id
        """, user_id, quiz_name, total_questions)
        return row['id']

async def get_active_quiz(user_id: int):
    async with pool.acquire() as conn:
        return await conn.fetchrow("""
            SELECT * FROM quizzes WHERE user_id = $1 AND is_active = TRUE
            ORDER BY started_at DESC LIMIT 1
        """, user_id)

async def save_question(session_id: int, q_num: int, question: str, 
                         a: str, b: str, c: str, d: str, correct: str):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO quiz_questions 
            (quiz_session_id, question_number, question_text, option_a, option_b, option_c, option_d, correct_answer)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, session_id, q_num, question, a, b, c, d, correct)

async def answer_question(session_id: int, q_num: int, user_answer: str):
    async with pool.acquire() as conn:
        q = await conn.fetchrow("""
            SELECT correct_answer FROM quiz_questions 
            WHERE quiz_session_id = $1 AND question_number = $2
        """, session_id, q_num)
        if not q:
            return None
        is_correct = user_answer.upper() == q['correct_answer'].upper()
        await conn.execute("""
            UPDATE quiz_questions SET user_answer = $1, is_correct = $2, answered_at = NOW()
            WHERE quiz_session_id = $3 AND question_number = $4
        """, user_answer, is_correct, session_id, q_num)
        if is_correct:
            await conn.execute("UPDATE quizzes SET correct_answers = correct_answers + 1 WHERE id = $1", session_id)
        else:
            await conn.execute("UPDATE quizzes SET wrong_answers = wrong_answers + 1 WHERE id = $1", session_id)
        return is_correct

async def finish_quiz(session_id: int):
    async with pool.acquire() as conn:
        quiz = await conn.fetchrow("SELECT * FROM quizzes WHERE id = $1", session_id)
        await conn.execute("""
            UPDATE quizzes SET is_active = FALSE, finished_at = NOW() WHERE id = $1
        """, session_id)
        await conn.execute("""
            UPDATE users SET
                total_quizzes_taken = total_quizzes_taken + 1,
                total_correct = total_correct + $2,
                total_wrong = total_wrong + $3
            WHERE user_id = $1
        """, quiz['user_id'], quiz['correct_answers'], quiz['wrong_answers'])
        return quiz

async def get_quiz_questions(session_id: int):
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT * FROM quiz_questions WHERE quiz_session_id = $1 ORDER BY question_number
        """, session_id)

# ==================== SETTINGS FUNCTIONS ====================

async def get_setting(key: str):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT value FROM bot_settings WHERE key = $1", key)
        return row['value'] if row else None

async def set_setting(key: str, value: str):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO bot_settings (key, value, updated_at) VALUES ($1, $2, NOW())
            ON CONFLICT (key) DO UPDATE SET value = $2, updated_at = NOW()
        """, key, value)
