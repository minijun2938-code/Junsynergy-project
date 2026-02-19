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
    """다크모드 완벽 대응 및 SaaS 스타일 UI"""
    st.set_page_config(
        page_title="엔무버 궁합 프로그램", 
        page_icon="🤝",
        layout="centered"
    )
    
    # CSS 변수를 활용하여 라이트/다크 모드 통합 대응
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Noto+Sans+KR:wght@300;400;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', 'Noto Sans KR', sans-serif;
        }

        /* 버튼 및 인터랙션 요소 */
        .stButton > button {
            width: 100%;
            border-radius: 8px;
            height: 3rem;
            font-weight: 600;
            transition: all 0.2s ease;
        }

        /* 강조 버튼 (SK Red) - 다크모드에서도 명확히 보이도록 설정 */
        div.stButton > button:first-child {
            background-color: #E1002A !important;
            color: #FFFFFF !important;
            border: none !important;
        }
        
        div.stButton > button:hover {
            box-shadow: 0 4px 15px rgba(225, 0, 42, 0.3);
            transform: translateY(-1px);
        }

        /* 카드형 섹션 - 다크모드 대응 컬러 */
        .card {
            padding: 2rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            border: 1px solid rgba(128, 128, 128, 0.2);
            background-color: rgba(255, 255, 255, 0.05);
        }

        /* 타이틀 디자인 */
        .header-title {
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -1px;
            text-align: center;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #E1002A 0%, #FF5E00 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .header-sub {
            font-size: 1rem;
            color: #888;
            text-align: center;
            margin-bottom: 3rem;
        }

        /* 탭 커스텀 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            padding: 4px;
            border-radius: 12px;
        }
        
        /* 설명 문구 */
        .description {
            font-size: 0.9rem;
            color: #888;
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }

        /* 다크모드 글자색 보정 */
        [data-testid="stMarkdownContainer"] p {
            color: inherit;
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
    new_team = st.text_input("팀 이름", placeholder="ex) 기업문화팀 (정확히 입력)")
    new_pw = st.text_input("비밀번호", type="password")
    
    st.divider()
    st.caption("개인정보 보호정책: 수집된 성향 데이터는 시너지 분석 목적으로만 사용되며, 언제든 파기 가능합니다.")
    agreed = st.checkbox("약관에 동의합니다.")
    
    if st.button("가입 완료", use_container_width=True):
        if not new_id or not new_name or not new_pw or not new_team:
            st.error("모든 정보를 입력해주세요.")
        elif not validate_emp_id(new_id):
            st.error("사번 형식이 올바르지 않습니다 (slXXXXX).")
        elif not agreed:
            st.warning("동의가 필요합니다.")
        else:
            if auth.register_user(new_id, new_pw, new_name, new_team.strip()):
                st.success("가입 성공! 로그인을 진행해주세요.")
                st.rerun()

def show_main_content(emp_id):
    user_info = db.get_user_info(emp_id)
    # user_info: (name, profile_data, last_sync, llm_name, team_name)
    user_name = user_info[0]
    user_team = user_info[4] if len(user_info) > 4 else "미소속"
    
    with st.sidebar:
        st.markdown(f"### 👤 {user_name}님")
        st.caption(f"사번: {emp_id}")
        st.caption(f"소속: {user_team}")
        st.divider()
        if st.button("로그아웃"):
            del st.session_state.logged_in_id
            st.rerun()

    # 알림 데이터 가져오기
    pending_requests = db.get_pending_requests(emp_id)
    notif_badge = f" 🔴 {len(pending_requests)}" if pending_requests else ""

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔒 데이터 등록", f"📩 파트너 매칭{notif_badge}", "📊 시너지 분석", "🏢 팀 분석", "👤 내 성향 분석"])

    with tab1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📋 내 성향 데이터 업데이트")
        
        if user_info and user_info[2]:
            st.caption(f"⏱ 마지막 동기화: {user_info[2]} ({user_info[3]})")
        else:
            st.caption("⏱ 동기화 이력 없음")

        st.markdown('<div class="description">외부 LLM을 통해 분석된 본인의 고유 성향 코드를 등록하세요. 기존 데이터가 있다면 새로운 내용으로 업데이트됩니다.</div>', unsafe_allow_html=True)
        
        selected_llm = st.selectbox("사용 중인 LLM을 선택해 주세요", ["ChatGPT", "Gemini", "Claude", "기타"], index=0)
        
        prompt_text = prompts.USER_ANALYSIS_PROMPT.replace("`", "\\`").replace("\n", "\\n")
        copy_code_html = f"""
            <div style="margin-bottom: 20px;">
                <button onclick="copyToClipboard()" style="
                    width: 100%;
                    background-color: #E1002A;
                    color: white;
                    border: none;
                    padding: 14px 20px;
                    border-radius: 10px;
                    font-weight: bold;
                    cursor: pointer;
                    font-size: 1.1rem;
                    box-shadow: 0 4px 12px rgba(225, 0, 42, 0.2);
                ">📋 {selected_llm}용 분석 문구 복사하기</button>
            </div>
            <script>
                function copyToClipboard() {{
                    const text = `[Target LLM: {selected_llm}]\\n\\n{prompt_text}`;
                    navigator.clipboard.writeText(text).then(function() {{
                        alert('{selected_llm}용 분석 문구가 복사되었습니다!');
                    }});
                }}
            </script>
        """
        st.components.v1.html(copy_code_html, height=80)
        
        raw_input = st.text_area("분석 결과는 타인이 볼 수 없습니다.", height=150, placeholder="영문/숫자 결과 코드를 붙여넣으세요.")
        
        sync_col1, sync_col2 = st.columns([1, 1])
        with sync_col1:
            if st.button("데이터 동기화", use_container_width=True):
                if not raw_input:
                    st.warning("코드를 입력해주세요.")
                else:
                    try:
                        # 1. 전처리: 불필요한 마크다운 코드 블록 태그 및 공백/줄바꿈 제거
                        cleaned_input = raw_input.strip()
                        if cleaned_input.startswith("```"):
                            cleaned_input = re.sub(r'^```[a-zA-Z0-9]*\n|```$', '', cleaned_input, flags=re.MULTILINE).strip()
                        
                        # Base64 문자열 내의 모든 공백 및 개행 제거 (더 견고한 처리)
                        cleaned_input = "".join(cleaned_input.split())
                        
                        # 2. Base64 디코딩 (Padding 보정 포함)
                        missing_padding = len(cleaned_input) % 4
                        if missing_padding:
                            cleaned_input += '=' * (4 - missing_padding)
                        
                        decoded_bytes = base64.b64decode(cleaned_input)
                        
                        # 3. 인코딩 감지 및 변환 (utf-8, cp949, euc-kr 등 대응)
                        try:
                            decoded_str = decoded_bytes.decode('utf-8')
                        except UnicodeDecodeError:
                            try:
                                decoded_str = decoded_bytes.decode('cp949') # 한글 윈도우 환경 고려
                            except UnicodeDecodeError:
                                decoded_str = decoded_bytes.decode('utf-8', errors='replace') # 깨진 글자 무시하고 최대한 복구
                        
                        # 4. JSON 검증 및 저장
                        try:
                            json_data = json.loads(decoded_str)
                        except json.JSONDecodeError:
                            match = re.search(r'\{.*\}', decoded_str, re.DOTALL)
                            if match:
                                json_data = json.loads(match.group())
                            else:
                                raise ValueError("JSON 형식을 찾을 수 없습니다.")

                        db.save_profile(emp_id, json.dumps(json_data, ensure_ascii=False), llm_name=selected_llm)
                        st.session_state.sync_success = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"유효하지 않은 코드 형식입니다. (상세: {str(e)})")
        
        with sync_col2:
            if st.session_state.get('sync_success'):
                st.markdown('<div style="color: #10b981; font-weight: bold; padding: 0.8rem 0;">✅ 데이터 동기화 성공!</div>', unsafe_allow_html=True)
                # 메시지 표시 후 상태 초기화 (원하는 경우)
                # st.session_state.sync_success = False 
        
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        
        # 1. 받은 요청
        if pending_requests:
            st.subheader(f"🔔 받은 매칭 요청 ({len(pending_requests)})")
            for req in pending_requests:
                c1, c2 = st.columns([3, 1])
                c1.write(f"👉 **{req[0]}** 님이 매칭을 요청했습니다.")
                if c2.button("수락", key=f"acc_{req[0]}"):
                    db.accept_match_request(req[0], emp_id)
                    st.rerun()
            st.divider()

        # 2. 보낸 요청 (철회 기능)
        sent_requests = db.get_sent_requests(emp_id)
        if sent_requests:
            st.subheader(f"📨 보낸 매칭 요청 ({len(sent_requests)})")
            for req in sent_requests:
                c1, c2 = st.columns([3, 1])
                c1.write(f"⌛ **{req[0]}** 님께 요청을 보냈습니다.")
                if c2.button("철회", key=f"can_{req[0]}", help="상대방이 수락하기 전까지 취소 가능"):
                    db.cancel_match_request(emp_id, req[0])
                    st.toast("요청이 철회되었습니다.")
                    st.rerun()
            st.divider()

        # 3. 새로운 요청 보내기
        st.subheader("➕ 새로운 파트너 매칭")
        target_id = st.text_input("상대방 사번", placeholder="slXXXXX")
        if st.button("매칭 요청 발송"):
            if not validate_emp_id(target_id):
                st.error("사번 형식을 확인해주세요.")
            elif target_id == emp_id:
                st.warning("본인에게는 요청할 수 없습니다.")
            else:
                db.send_match_request(emp_id, target_id)
                st.success("요청 완료!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📊 시너지 리포트 센터")
        
        accepted = db.get_accepted_matches(emp_id)
        if not accepted:
            st.info("현재 매칭된 파트너가 없습니다.")
        else:
            other_ids = list(set([m[0] if m[1] == emp_id else m[1] for m in accepted]))
            
            # 파트너 이름 매핑 생성
            partner_options = {}
            for oid in other_ids:
                u_info = db.get_user_info(oid)
                # u_info가 없을 경우 대비 (삭제된 유저 등)
                if u_info:
                    display_label = f"{u_info[0]} ({oid})"
                    partner_options[display_label] = oid
            
            if not partner_options:
                st.warning("유효한 파트너 정보를 불러올 수 없습니다.")
            else:
                selected_label = st.selectbox("분석 대상 선택", list(partner_options.keys()))
                selected_other = partner_options[selected_label]
                
                st.write("")
                mode = st.radio("분석 관점 선택", ["직장 동료", "연인 궁합", "상사-부하"], horizontal=True)
                
                additional_info = {}
                can_proceed = True
                
                if mode == "연인 궁합":
                    st.markdown("---")
                    cg1, cg2 = st.columns(2)
                    additional_info['gender_a'] = cg1.selectbox(f"내({user_name}) 성별", ["선택", "남성", "여성"])
                    additional_info['gender_b'] = cg2.selectbox(f"상대방 성별", ["선택", "남성", "여성"])
                    if "선택" in [additional_info['gender_a'], additional_info['gender_b']]:
                        can_proceed = False
                elif mode == "상사-부하":
                    st.markdown("---")
                    other_name = db.get_user_info(selected_other)[0]
                    superior = st.selectbox("누가 리더(상사)인가요?", [user_name, other_name])
                    additional_info['superior_name'] = superior
                    additional_info['subordinate_name'] = other_name if superior == user_name else user_name

                if st.button("시너지 분석 시작", disabled=not can_proceed):
                    info_a = db.get_user_info(emp_id)
                    info_b = db.get_user_info(selected_other)
                    mode_map = {"직장 동료": "colleague", "연인 궁합": "couple", "상사-부하": "hierarchy"}
                    with st.spinner("🔍 분석 중..."):
                        report = ai_engine.analyze_compatibility(info_a[1], info_b[1], info_a[0], info_b[0], mode=mode_map[mode], additional_info=additional_info)
                    st.markdown("---")
                    st.markdown(report)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab4:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader(f"🏢 팀 분석 ({user_team})")
        
        if not user_team or user_team == "미소속":
             st.warning("소속된 팀 정보가 없습니다.")
        else:
            team_members = db.get_team_members(user_team)
            # team_members: list of (name, profile_data, emp_id)
            
            if len(team_members) < 2:
                st.info(f"현재 {user_team}에 등록된 멤버가 부족합니다. (최소 2명 이상 필요)")
            else:
                member_names = [m[0] for m in team_members]
                st.write(f"**현재 등록된 멤버 ({len(member_names)}명):** {', '.join(member_names)}")
                
                leader_name = st.selectbox("이 팀의 리더(팀장)는 누구인가요?", member_names)
                
                if st.button("🚀 팀 전체 시너지 분석"):
                    with st.spinner("팀 역학 관계 및 시너지 분석 중..."):
                        # 멤버 데이터를 AI 엔진에 전달 (튜플 리스트 그대로 전달)
                        # 필요한 것: name, profile_data
                        # team_members 구조: [(name, data, id), ...]
                        # ai_engine 함수 호출
                        data_for_ai = [(m[0], m[1], m[2]) for m in team_members]
                        report = ai_engine.analyze_team_synergy(data_for_ai, user_team, leader_name)
                    
                    st.markdown("---")
                    st.markdown(report)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab5:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("👤 개인 성향 심층 분석")
        info_self = db.get_user_info(emp_id)
        if not info_self[1]:
            st.warning("데이터 등록 탭에서 먼저 정보를 입력해주세요.")
        else:
            gender = st.radio("성별 (분석용)", ["남성", "여성"], horizontal=True)
            st.write("")
            btn_cols = st.columns(3)
            report_type = None
            if btn_cols[0].button("🧩 MBTI 분석", use_container_width=True): report_type = "self_mbti"
            if btn_cols[1].button("🎭 에겐테토분석", use_container_width=True): report_type = "self_archetype"
            if btn_cols[2].button("🌟 장단점 분석", use_container_width=True): report_type = "self_swot"
            
            if report_type:
                with st.spinner("🔍 분석 중..."):
                    report = ai_engine.analyze_compatibility(info_self[1], None, info_self[0], None, mode=report_type, additional_info={"gender": gender})
                st.markdown("---")
                st.markdown(report)
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