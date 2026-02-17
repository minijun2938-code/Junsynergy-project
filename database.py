import sqlite3

def get_connection():
    return sqlite3.connect('poc_chemistry.db')

def init_db():
    with get_connection() as conn:
        c = conn.cursor()
        # 'name' 컬럼이 포함된 테이블 생성
        c.execute('''CREATE TABLE IF NOT EXISTS user_profiles 
                     (emp_id TEXT PRIMARY KEY, password TEXT, name TEXT, profile_data TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS matches 
                     (req_id TEXT, target_id TEXT, status TEXT, UNIQUE(req_id, target_id))''')
        conn.commit()

def save_profile(emp_id, profile_json):
    """프로필 데이터를 저장합니다. 이미 존재한다면 업데이트합니다."""
    with get_connection() as conn:
        c = conn.cursor()
        # 데이터 동기화 이슈 해결: 기존 데이터가 있으면 UPDATE, 없으면 IGNORE (보통 로그인이 된 상태이므로 UPDATE가 맞음)
        c.execute("UPDATE user_profiles SET profile_data = ? WHERE emp_id = ?", (profile_json, emp_id))
        conn.commit()

def get_user_info(emp_id):
    """사번으로 이름과 성향 데이터를 한꺼번에 가져옵니다."""
    with get_connection() as conn:
        c = conn.cursor()
        return c.execute("SELECT name, profile_data FROM user_profiles WHERE emp_id=?", (emp_id,)).fetchone()

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