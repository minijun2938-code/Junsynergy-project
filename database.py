import sqlite3
from datetime import datetime

def get_connection():
    return sqlite3.connect('poc_chemistry.db')

def init_db():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS user_profiles 
                     (emp_id TEXT PRIMARY KEY, 
                      password TEXT, 
                      name TEXT, 
                      profile_data TEXT,
                      last_sync TEXT,
                      llm_name TEXT)''')
        
        # 기존 테이블에 새 컬럼이 없을 경우 추가 (Migration)
        try:
            c.execute("ALTER TABLE user_profiles ADD COLUMN last_sync TEXT")
        except: pass
        try:
            c.execute("ALTER TABLE user_profiles ADD COLUMN llm_name TEXT")
        except: pass
        
        c.execute('''CREATE TABLE IF NOT EXISTS matches 
                     (req_id TEXT, target_id TEXT, status TEXT, UNIQUE(req_id, target_id))''')
        conn.commit()

def save_profile(emp_id, profile_json, llm_name=None):
    """프로필 데이터를 저장합니다. 이미 존재한다면 업데이트합니다."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""UPDATE user_profiles 
                     SET profile_data = ?, last_sync = ?, llm_name = ? 
                     WHERE emp_id = ?""", 
                  (profile_json, now, llm_name, emp_id))
        conn.commit()

def get_user_info(emp_id):
    """사번으로 이름과 성향 데이터를 한꺼번에 가져옵니다."""
    with get_connection() as conn:
        c = conn.cursor()
        return c.execute("SELECT name, profile_data, last_sync, llm_name FROM user_profiles WHERE emp_id=?", (emp_id,)).fetchone()

def send_match_request(req_id, target_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO matches VALUES (?, ?, ?)", (req_id, target_id, 'Pending'))
        conn.commit()

def get_pending_requests(emp_id):
    with get_connection() as conn:
        c = conn.cursor()
        return c.execute("SELECT req_id FROM matches WHERE target_id=? AND status='Pending'", (emp_id,)).fetchall()

def accept_match_request(req_id, target_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("UPDATE matches SET status='Accepted' WHERE req_id=? AND target_id=?", (req_id, target_id))
        conn.commit()

def get_accepted_matches(emp_id):
    with get_connection() as conn:
        c = conn.cursor()
        return c.execute("""SELECT req_id, target_id FROM matches 
                            WHERE (req_id=? OR target_id=?) AND status='Accepted'""", 
                         (emp_id, emp_id)).fetchall()