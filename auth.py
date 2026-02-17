import hashlib
from database import get_connection

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_login(emp_id, password):
    with get_connection() as conn:
        c = conn.cursor()
        user = c.execute("SELECT password FROM user_profiles WHERE emp_id=?", (emp_id,)).fetchone()
        if user:
            return user[0] == hash_password(password)
        return None

def register_user(emp_id, password, name):
    with get_connection() as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO user_profiles (emp_id, password, name) VALUES (?, ?, ?)", 
                      (emp_id, hash_password(password), name))
            conn.commit()
            return True
        except:
            return False