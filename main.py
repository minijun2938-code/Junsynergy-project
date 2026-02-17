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
    """전문적인 SaaS 느낌의 클린 UI 스타일링"""
    st.set_page_config(
        page_title="엔무버 궁합 프로그램", 
        page_icon="🤝",
        layout="centered"
    )
    
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Noto+Sans+KR:wght@300;400;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', 'Noto Sans KR', sans-serif;
        }

        .main {
            background-color: #fcfcfc;
        }

        /* 메인 컬러: SK Red 포인트 */
        :root {
            --primary: #E1002A;
            --primary-light: #FFEBEE;
            --text-main: #1A1A1A;
            --text-sub: #666666;
            --bg-card: #FFFFFF;
        }

        /* 버튼 스타일 최적화 */
        .stButton > button {
            width: 100%;
            border-radius: 8px;
            height: 3rem;
            font-weight: 600;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid #E0E0E0;
            background-color: white;
            color: var(--text-main);
        }

        /* 강조 버튼 (SK Red) */
        div.stButton > button:first-child {
            background-color: var(--primary);
            color: white;
            border: none;
        }
        
        div.stButton > button:hover {
            box-shadow: 0 4px 12px rgba(225, 0, 42, 0.15);
            transform: translateY(-1px);
            opacity: 0.95;
        }

        /* 카드형 섹션 */
        .card {
            background-color: var(--bg-card);
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02), 0 12px 24px rgba(0,0,0,0.03);
            margin-bottom: 2rem;
            border: 1px solid #F0F0F0;
        }

        /* 타이틀 디자인 */
        .header-title {
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -1px;
            color: var(--text-main);
            text-align: center;
            margin-bottom: 0.5rem;
        }
        
        .header-sub {
            font-size: 1rem;
            color: var(--text-sub);
            text-align: center;
            margin-bottom: 3rem;
        }

        /* 탭 커스텀 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            padding: 4px;
            background-color: #F5F5F5;
            border-radius: 12px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            font-weight: 600;
            color: #888;
        }
        .stTabs [aria-selected="true"] {
            background-color: white !important;
            color: var(--primary) !important;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        }

        /* 입력 폼 */
        div[data-baseweb="input"] {
            border-radius: 8px;
            border: 1px solid #E0E0E0;
        }

        /* 설명 문구 */
        .description {
            font-size: 0.9rem;
            color: var(--text-sub);
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }
        </style>
    """, unsafe_allow_html=True)

def validate_emp_id(emp_id):
    pattern = r'^sl\d{5}$'
    return re.match(pattern, emp_id) is not None

def show_login_page():
    st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="header-title">엔무버 궁합 프로그램</div>', unsafe_allow_html=True)
    st.markdown('<div class="header-sub">Professional Synergy Analysis Tool for Enmovers</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        user_id = st.text_input("사번 (sl+5자리)", placeholder="sl12345")
        user_pw = st.text_input("비밀번호", type="password", placeholder="••••••••")
        
        if st.button("로그인", use_container_width=True):
            if auth.check_login(user_id, user_pw):
                st.session_state.logged_in_id = user_id
                st.rerun()
            else:
                st.error("사번 또는 비밀번호를 확인해주세요.")
        
        st.markdown('<div style="text-align: center; margin-top: 1.5rem;">', unsafe_allow_html=True)
        if st.button("신규 구성원 가입", key="signup_btn"):
            signup_dialog()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

@st.dialog("신규 구성원 가입")
def signup_dialog():
    st.markdown("### 📝 구성원 등록")
    new_id = st.text_input("사번 (Emp ID)", placeholder="sl12345")
    new_name = st.text_input("이름", placeholder="성함을 입력하세요")
    new_pw = st.text_input("비밀번호", type="password")
    
    st.divider()
    st.caption("개인정보 보호정책: 수집된 성향 데이터는 시너지 분석 목적으로만 사용되며, 언제든 파기 가능합니다.")
    agreed = st.checkbox("약관에 동의합니다.")
    
    if st.button("가입 완료", use_container_width=True):
        if not new_id or not new_name or not new_pw:
            st.error("모든 정보를 입력해주세요.")
        elif not validate_emp_id(new_id):
            st.error("사번 형식이 올바르지 않습니다 (slXXXXX).")
        elif not agreed:
            st.warning("동의가 필요합니다.")
        else:
            if auth.register_user(new_id, new_pw, new_name):
                st.success("가입 성공! 로그인을 진행해주세요.")
                st.rerun()

def show_main_content(emp_id):
    user_info = db.get_user_info(emp_id)
    
    with st.sidebar:
        st.markdown(f"### 👤 {user_info[0]}님")
        st.caption(f"사번: {emp_id}")
        st.divider()
        if st.button("로그아웃"):
            del st.session_state.logged_in_id
            st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["🔒 데이터 등록", "📩 파트너 매칭", "📊 시너지 분석", "👤 내 성향 분석"])

    with tab1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📋 성향 암호화 코드 등록")
        st.markdown('<div class="description">외부 LLM을 통해 분석된 본인의 고유 성향 코드를 등록하세요. 이 데이터는 파트너와 매칭될 때 시너지 리포트의 핵심 재료로 사용됩니다.</div>', unsafe_allow_html=True)
        
        with st.expander("🛠 코드 생성을 위한 보안 프롬프트 복사"):
            st.write("아래 프롬프트 전체를 복사하여 ChatGPT나 Gemini에 입력하세요. 분석 결과로 나오는 암호화 코드를 아래에 붙여넣어 주시면 됩니다.")
            st.code(prompts.USER_ANALYSIS_PROMPT, language="text")
        
        raw_input = st.text_area("보안 결과 코드 (Base64)", height=120, placeholder="영문/숫자로 구성된 결과 코드를 붙여넣으세요.")
        if st.button("데이터 동기화"):
            try:
                decoded_str = base64.b64decode(raw_input).decode('utf-8')
                json.loads(decoded_str)
                db.save_profile(emp_id, decoded_str)
                st.success("데이터가 안전하게 저장되었습니다.")
                st.balloons()
            except:
                st.error("올바른 코드 형식이 아닙니다.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📩 협업 파트너 매칭")
        st.markdown('<div class="description">함께 일하는 동료와의 업무 궁합이나 관계 역동을 확인하고 싶으신가요? 상대방의 사번을 입력해 요청을 보내보세요.</div>', unsafe_allow_html=True)
        
        target_id = st.text_input("상대방 사번", placeholder="slXXXXX")
        if st.button("매칭 요청 발송"):
            if not validate_emp_id(target_id):
                st.error("사번 형식을 확인해주세요.")
            elif target_id == emp_id:
                st.warning("자기 자신은 매칭할 수 없습니다.")
            else:
                db.send_match_request(emp_id, target_id)
                st.success("요청 완료! 상대방이 수락하면 분석이 가능합니다.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📊 시너지 리포트 센터")
        
        pending = db.get_pending_requests(emp_id)
        if pending:
            st.markdown("#### 🔔 수락 대기 중")
            for req in pending:
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{req[0]}** 님의 매칭 요청")
                if c2.button("수락", key=f"acc_{req[0]}"):
                    db.accept_match_request(req[0], emp_id)
                    st.rerun()
            st.divider()

        accepted = db.get_accepted_matches(emp_id)
        if not accepted:
            st.info("현재 매칭된 파트너가 없습니다. 파트너 매칭 탭을 이용해보세요.")
        else:
            other_ids = list(set([m[0] if m[1] == emp_id else m[1] for m in accepted]))
            selected_other = st.selectbox("분석 대상 선택", other_ids)
            
            st.write("")
            mode = st.radio("분석 관점 선택", ["직장 동료", "연인 궁합", "상사-부하"], horizontal=True)
            
            additional_info = {}
            can_proceed = True
            
            if mode == "연인 궁합":
                st.markdown("---")
                cg1, cg2 = st.columns(2)
                additional_info['gender_a'] = cg1.selectbox(f"내({user_info[0]}) 성별", ["선택", "남성", "여성"])
                additional_info['gender_b'] = cg2.selectbox(f"상대방 성별", ["선택", "남성", "여성"])
                if "선택" in [additional_info['gender_a'], additional_info['gender_b']]:
                    can_proceed = False
            elif mode == "상사-부하":
                st.markdown("---")
                superior = st.selectbox("누가 리더(상사)인가요?", [user_info[0], db.get_user_info(selected_other)[0]])
                additional_info['superior_name'] = superior
                additional_info['subordinate_name'] = [user_info[0], db.get_user_info(selected_other)[0]]
                additional_info['subordinate_name'].remove(superior)
                additional_info['subordinate_name'] = additional_info['subordinate_name'][0]

            if st.button("전문 AI 분석 시작", disabled=not can_proceed):
                info_a = db.get_user_info(emp_id)
                info_b = db.get_user_info(selected_other)
                mode_map = {"직장 동료": "colleague", "연인 궁합": "couple", "상사-부하": "hierarchy"}
                with st.status("🔍 정밀 분석 리포트 생성 중..."):
                    report = ai_engine.analyze_compatibility(info_a[1], info_b[1], info_a[0], info_b[0], mode=mode_map[mode], additional_info=additional_info)
                st.markdown("---")
                st.markdown(report)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab4:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("👤 개인 성향 심층 분석")
        st.markdown('<div class="description">본인의 데이터를 기반으로 MBTI 유형과 최신 트렌드 바이브를 정밀하게 진단합니다.</div>', unsafe_allow_html=True)
        
        info_self = db.get_user_info(emp_id)
        if not info_self[1]:
            st.warning("데이터 등록 탭에서 먼저 정보를 입력해주세요.")
        else:
            gender = st.radio("성별 (에겐테토 분석용)", ["남성", "여성"], horizontal=True)
            st.write("")
            
            # 버튼 3개를 하나의 로우에 꽉 차게 배치
            btn_cols = st.columns(3)
            report_type = None
            
            with btn_cols[0]:
                if st.button("🧩 MBTI 분석", use_container_width=True):
                    report_type = "self_mbti"
            with btn_cols[1]:
                if st.button("🎭 에겐테토분석", use_container_width=True):
                    report_type = "self_archetype"
            with btn_cols[2]:
                if st.button("🌟 장단점 분석", use_container_width=True):
                    report_type = "self_swot"
            
            if report_type:
                with st.status("🔍 AI가 심층 성향을 분석하고 있습니다..."):
                    report = ai_engine.analyze_compatibility(
                        info_self[1], None, info_self[0], None, 
                        mode=report_type, 
                        additional_info={"gender": gender}
                    )
                st.markdown("---")
                st.markdown(report)
                st.download_button(
                    label="📥 분석 리포트 저장 (Markdown)", 
                    data=report, 
                    file_name=f"Self_Analysis_{report_type}_{emp_id}.md"
                )
        st.markdown('</div>', unsafe_allow_html=True)
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