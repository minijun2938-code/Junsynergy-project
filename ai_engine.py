import os
import google.generativeai as genai
from dotenv import load_dotenv
import prompts

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

def analyze_compatibility(data_a, data_b, name_a, name_b, mode="colleague", additional_info=None):
    if not api_key:
        return "❌ API 키가 설정되지 않았습니다."

    genai.configure(api_key=api_key, transport='rest')
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # 모드에 따른 시스템 프롬프트 및 추가 컨텍스트 설정
    if mode == "couple":
        system_prompt = prompts.COUPLE_PROMPT
        gender_a = additional_info.get('gender_a', '미설정')
        gender_b = additional_info.get('gender_b', '미설정')
        context_text = f"""
        [관계 유형: 연인]
        - A: {name_a}({gender_a})
        - B: {name_b}({gender_b})
        - 특별 지시: 업무 성과가 아닌 '성격적 끌림'과 '감정적 교류'에 초점을 맞추세요. 
        점수는 '연애 케미'라는 이름으로 동료 점수와는 완전히 다른 로직(성격의 보완성, 대화의 즐거움 등)으로 매기세요.
        """
    elif mode == "hierarchy":
        system_prompt = prompts.HIERARCHY_PROMPT
        superior = additional_info.get('superior_name', '상사')
        subordinate = additional_info.get('subordinate_name', '부하')
        context_text = f"""
        [관계 유형: 상사-부하]
        - 상사: {superior}
        - 부하: {subordinate}
        - 특별 지시: '지시와 보고'의 효율성, '신뢰 관계 구축'에 초점을 맞추어 분석하세요.
        """
    elif mode == "self_mbti":
        system_prompt = prompts.SELF_MBTI_PROMPT
        gender = additional_info.get('gender', '미설정')
        context_text = f"[분석 유형: MBTI & 아키타입 추측] 대상자: {name_a} ({gender})"
    elif mode == "self_swot":
        system_prompt = prompts.SELF_SWOT_PROMPT
        gender = additional_info.get('gender', '미설정')
        context_text = f"[분석 유형: 장단점 분석] 대상자: {name_a} ({gender})"
    else:
        system_prompt = prompts.COLLEAGUE_PROMPT
        context_text = f"""
        [관계 유형: 직장 동료]
        - 특별 지시: '공동의 목표 달성'과 '업무 스타일의 조화'에 집중하여 분석하세요.
        """

    if mode.startswith("self"):
        user_content = f"""
        {context_text}
        [성향 데이터 원문]
        - {name_a}: {data_a}
        
        위 데이터를 바탕으로 전문적인 리포트를 작성해줘. 
        가독성을 위해 헤딩(###)과 이모지를 적극 활용하세요.
        """
    else:
        user_content = f"""
        {context_text}
        [성향 데이터 원문]
        - 대상자 A({name_a}): {data_a}
        - 대상자 B({name_b}): {data_b}
        
        위 데이터를 바탕으로 선택된 모드에 맞는 리포트를 작성해줘. 
        **중요: 각 모드별로 완전히 다른 페르소나와 점수 산출 방식을 적용하여 결과가 중복되지 않게 하세요.**
        가독성을 위해 헤딩(###)과 이모지를 적극 활용하세요.
        """
    
    try:
        response = model.generate_content([system_prompt, user_content])
        return response.text
    except Exception as e:
        return f"⚠️ AI 분석 중 오류 발생: {str(e)}"