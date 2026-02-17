import streamlit as st
import json
import base64
import database as db
import auth
import ai_engine
import prompts
import re
from datetime import datetime

# --- UI 세션 상태 초기화 ---
if 'view' not in st.session_state:
    st.session_state.view = 'login'

def set_page_style():
    """프로덕션 수준의 고퀄리티 UI 스타일링"""
    st.set_page_config(
        page_title="Chemistry Hub | Team Synergy Analysis", 
        page_icon="🤝",
        layout="centered"
    )
    
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700&display=swap');
        
        * {
            font-family: 'Pretendard', sans-serif;
        }

        .main {
            background-color: #f8f9fa;
        }

        .stButton > button {
            width: 100%;
            border-radius: 10px;
            height: 3.2rem;
            font-weight: 600;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            border: none;
        }

        div.stButton > button:first-child {
            background-color: #111827;
            color: white;
        }
        
        div.stButton > button:hover {
            background-color: #1f2937;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transform: translateY(-1px);
        }

        .card {
            background-color: white;
            padding: 32px;
            border-radius: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 20px 25px -5px rgba(0,0,0,0.05);
            margin-bottom: 24px;
            border: 1px solid #f3f4f6;
        }

        .header-title {
            font-size: 2.4rem;
            font-weight: 800;
            letter-spacing: -1px;
            color: #111827;
            margin-bottom: 12px;
            text-align: center;
        }
        
        .header-sub {
            font-size: 1.1rem;
            color: #6b7280;
            margin-bottom: 40px;
            text-align: center;
        }

        .privacy-box {
            font-size: 0.85rem;
            color: #6b7280;
            background-color: #f9fafb;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #e5e7eb;
            margin-bottom: 20px;
            height: 150px;
            overflow-y: scroll;
        }

        /* 케이스 선택 버튼 스타일 */
        .mode-container {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

def validate_emp_id(emp_id):
    pattern = r'^sl\d{5}$'
    return re.match(pattern, emp_id) is not None

PRIVACY_POLICY = """
[개인정보 수집 및 이용 동의서]
1. 수집 항목: 사번, 성명, 비밀번호, AI 성향 분석 데이터.
2. 이용 목적: 동료/연인/조직 간 성향 분석 및 시너지 리포트 생성.
3. 보유 기간: 회원 탈퇴 시 즉시 파기.
4. 보안 조치: 데이터 암호화 저장 및 일시적 복호화 분석.
"""

@st.dialog("신규 계정 생성 및 약관 동의")
def signup_dialog():
    st.markdown("### 📝 회원가입")
    new_id = st.text_input("사번 (Emp ID)", placeholder="예: sl12345")
    new_name = st.text_input("이름", placeholder="실명을 입력하세요")
    new_pw = st.text_input("비밀번호", type="password")
    st.markdown(f'<div class="privacy-box">{PRIVACY_POLICY}</div>', unsafe_allow_html=True)
    agreed = st.checkbox("위 개인정보 수집 및 이용에 동의합니다. (필수)")
    if st.button("가입 신청하기", use_container_width=True):
        if not new_id or not new_name or not new_pw:
            st.error("모든 항목을 입력해 주세요.")
        elif not validate_emp_id(new_id):
            st.error("사번 형식이 올바르지 않습니다. (sl + 숫자 5자리)")
        elif not agreed:
            st.warning("이용 약관에 동의해 주세요.")
        else:
            if auth.register_user(new_id, new_pw, new_name):
                st.success("회원가입 완료!")
                st.rerun()
            else:
                st.error("이미 등록된 사번이거나 오류가 발생했습니다.")

def show_login_page():
    st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="header-title">🤝 Chemistry Hub</div>', unsafe_allow_html=True)
    st.markdown('<div class="header-sub">Advanced Synergy Analysis System</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### Login")
        user_id = st.text_input("사번", placeholder="sl12345", label_visibility="collapsed")
        user_pw = st.text_input("비밀번호", type="password", placeholder="••••••••", label_visibility="collapsed")
        if st.button("로그인", use_container_width=True):
            if auth.check_login(user_id, user_pw):
                st.session_state.logged_in_id = user_id
                st.rerun()
            else:
                st.error("로그인 정보가 일치하지 않습니다.")
        st.divider()
        if st.button("신규 회원가입", key="signup_btn"):
            signup_dialog()
        st.markdown('</div>', unsafe_allow_html=True)

def show_main_content(emp_id):
    user_info = db.get_user_info(emp_id)
    with st.container():
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(f"### 👋 Welcome back, **{user_info[0]}**님")
        with c2:
            if st.button("로그아웃", key="logout"):
                del st.session_state.logged_in_id
                st.rerun()
    
    tab1, tab2, tab3, tab4 = st.tabs(["🔒 데이터 등록", "📩 파트너 매칭", "📊 시너지 분석", "👤 내 성향 분석"])

    with tab1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📋 성향 암호화 코드 등록")
        with st.expander("🛠 분석용 프롬프트 복사"):
            st.code(prompts.USER_ANALYSIS_PROMPT, language="text")
        raw_input = st.text_area("보안 코드 (Base64)", height=150)
        if st.button("✨ 데이터 동기화"):
            try:
                decoded_str = base64.b64decode(raw_input).decode('utf-8')
                json.loads(decoded_str)
                db.save_profile(emp_id, decoded_str)
                st.success("안전하게 저장되었습니다!")
                st.balloons()
            except:
                st.error("유효하지 않은 형식입니다.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📩 협업 파트너 요청")
        target_id = st.text_input("상대방 사번", placeholder="예: sl54321")
        if st.button("📨 매칭 요청 발송"):
            if not validate_emp_id(target_id):
                st.error("sl + 숫자 5자리 형식을 확인하세요.")
            elif target_id == emp_id:
                st.warning("본인에게는 요청할 수 없습니다.")
            else:
                db.send_match_request(emp_id, target_id)
                st.success("요청이 완료되었습니다.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📊 맞춤형 시너지 분석")
        
        # 요청 승인 관리
        pending = db.get_pending_requests(emp_id)
        if pending:
            st.markdown("#### 🔔 대기 중인 요청")
            for req in pending:
                ic1, ic2 = st.columns([3, 1])
                with ic1: st.write(f"👉 **{req[0]}** 님의 요청")
                with ic2:
                    if st.button("수락", key=f"acc_{req[0]}"):
                        db.accept_match_request(req[0], emp_id)
                        st.rerun()
            st.divider()

        accepted = db.get_accepted_matches(emp_id)
        if not accepted:
            st.info("매칭된 파트너가 없습니다.")
        else:
            other_ids = list(set([m[0] if m[1] == emp_id else m[1] for m in accepted]))
            selected_other = st.selectbox("분석 대상 선택", other_ids)
            
            st.markdown("---")
            st.write("🎯 **분석 케이스 선택**")
            mode = st.radio("어떤 궁합을 확인하고 싶으신가요?", 
                           ["직장 동료", "연인 궁합", "상사-부하"], 
                           horizontal=True)
            
            additional_info = {}
            can_proceed = True
            
            if mode == "연인 궁합":
                st.write("🚻 **성별 정보를 입력해 주세요.**")
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    additional_info['gender_a'] = st.selectbox(f"나({user_info[0]})의 성별", ["선택 안함", "남성", "여성"])
                with col_g2:
                    other_info = db.get_user_info(selected_other)
                    additional_info['gender_b'] = st.selectbox(f"상대방({other_info[0]})의 성별", ["선택 안함", "남성", "여성"])
                
                if additional_info['gender_a'] == "선택 안함" or additional_info['gender_b'] == "선택 안함":
                    st.warning("두 분의 성별을 모두 선택해야 분석이 가능합니다.")
                    can_proceed = False
                    
            elif mode == "상사-부하":
                st.write("👑 **역할을 설정해 주세요.**")
                other_info = db.get_user_info(selected_other)
                roles = [user_info[0], other_info[0]]
                superior = st.selectbox("누가 상사인가요?", roles)
                additional_info['superior_name'] = superior
                additional_info['subordinate_name'] = roles[1] if superior == roles[0] else roles[0]

            if st.button("🚀 맞춤형 AI 분석 시작", disabled=not can_proceed):
                info_a = db.get_user_info(emp_id)
                info_b = db.get_user_info(selected_other)
                
                if not info_a[1] or not info_b[1]:
                    st.error("두 사용자 모두 성향 데이터가 등록되어 있어야 합니다.")
                else:
                    mode_map = {"직장 동료": "colleague", "연인 궁합": "couple", "상사-부하": "hierarchy"}
                    with st.status("🔍 케이스별 알고리즘 분석 중...") as status:
                        report = ai_engine.analyze_compatibility(
                            info_a[1], info_b[1], info_a[0], info_b[0], 
                            mode=mode_map[mode], additional_info=additional_info
                        )
                        status.update(label="분석 완료!", state="complete")
                    
                    st.markdown("---")
                    st.markdown(report)
                    st.download_button("📥 리포트 저장", report, file_name=f"Chemistry_{mode}_{selected_other}.md")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab4:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("👤 개인 성향 심층 분석")
        st.write("등록된 내 데이터를 바탕으로 AI가 성향 및 MZ 아키타입을 정밀 분석합니다.")
        
        info_self = db.get_user_info(emp_id)
        
        if not info_self[1]:
            st.warning("먼저 '데이터 등록' 탭에서 성향 데이터를 입력해 주세요.")
        else:
            # 성별 선택 추가
            gender = st.radio("본인의 성별을 선택해 주세요", ["남성", "여성"], horizontal=True)
            
            # 버튼은 2열로 배치
            col_s1, col_s2 = st.columns(2)
            
            report_type = None
            if col_s1.button("🧩 내 MBTI & 아키타입 추측", use_container_width=True):
                report_type = "self_mbti"
            if col_s2.button("🌟 장단점 심층 분석", use_container_width=True):
                report_type = "self_swot"
            
            # 출력은 컬럼 밖에서 (전체 너비 사용)
            if report_type:
                with st.status("🔍 데이터를 정밀하게 분석하고 있습니다...") as status:
                    report = ai_engine.analyze_compatibility(
                        info_self[1], None, info_self[0], None, 
                        mode=report_type, 
                        additional_info={"gender": gender}
                    )
                    status.update(label="분석 완료!", state="complete")
                
                st.markdown("---")
                st.markdown(report)
                st.download_button(
                    label="📥 개인 분석 리포트 저장", 
                    data=report, 
                    file_name=f"Self_Analysis_{report_type}_{emp_id}.md"
                )
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    set_page_style()
    db.init_db()
    if 'logged_in_id' not in st.session_state:
        show_login_page()
    else:
        show_main_content(st.session_state.logged_in_id)

if __name__ == "__main__":
    main()