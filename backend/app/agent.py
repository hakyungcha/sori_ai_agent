from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Dict

from .schemas import ChatTurn, DistressLevel, SuicideSignal, NextAction, EndReport, TurnAnalysis


SUICIDE_HIGH = [
    "자살",
    "죽고 싶",
    "죽고싶",   # 공백 없이 입력하는 경우까지 포함
    "죽고싶어",  # 자주 쓰는 변형
    "죽을래",
    "끝내고 싶",
    "끝내고싶",
    "목숨",
    "살고 싶지",
    "살고싶지",
]
SUICIDE_MID = [
    "사라지고 싶",
    "포기하고 싶",
    "의미없",
    "그만 살",
]
DISTRESS_CUES = [
    "힘들",
    "괴롭",
    "불안",
    "우울",
    "외롭",
    "짜증",
    "분노",
    "무시",
    "따돌",
    "괴롭힘",
    "헛소문",
]
INTENSIFIERS = ["너무", "정말", "진짜", "완전", "계속"]
GREETING_CUES = [
    "안녕",
    "하이",
    "헬로",
    "hey",
    "hi",
]
BULLYING_CUES = [
    "괴롭힘",
    "괴롭",
    "따돌",
    "폭력",
    "폭행",
    "때렸",
    "맞았",
    "맞아",
    "두들겨",
]
GIVING_UP_CUES = [
    "이대로 지내",
    "그냥 지내",
    "참고 살",
    "참고 지내",
    "그냥 살",
    "포기",
    "그만",
    "그냥 이대로",
    "낫지 않을까",
    "그냥 참고",
]
SHORT_NEGATIVE_RESPONSES = ["싫어", "없어", "몰라", "아니야", "안돼"]
END_KEYWORDS = ["그만", "종료", "끝낼래", "끝", "다음에", "나중에", "그만할래", "끝내자", "대화 끝"]
POSITIVE_END = ["고마워", "도움됐어", "이제 괜찮아", "좋아졌어", "감사해", "고마웠어"]


@dataclass
class Analysis:
    emotional_distress: DistressLevel
    suicide_signal: SuicideSignal
    risk_score: int
    next_action: NextAction
    reply: str


def _contains_any(text: str, keywords: List[str]) -> bool:
    return any(word in text for word in keywords)

def _pick_non_repeating(candidates: List[str], recent_ai: List[str]) -> str:
    """최근 AI 발화와 겹치지 않는 답변을 우선 선택."""
    for candidate in candidates:
        if candidate not in recent_ai:
            return candidate
    return candidates[0] if candidates else ""

def _recent_ai_has_any(recent_ai: List[str], phrases: List[str]) -> bool:
    return any(any(p in text for p in phrases) for text in recent_ai)

def _is_end_request(message: str, history_len: int) -> bool:
    message_normalized = message.replace(" ", "").lower()
    for keyword in END_KEYWORDS:
        if keyword in message_normalized:
            return True
    if history_len >= 6:
        for keyword in POSITIVE_END:
            if keyword in message_normalized:
                return True
    return False


def _count_hits(text: str, keywords: List[str]) -> int:
    return sum(1 for word in keywords if word in text)


def _estimate_distress(text: str) -> DistressLevel:
    hits = _count_hits(text, DISTRESS_CUES)
    intense = _contains_any(text, INTENSIFIERS)
    if hits >= 3 or (hits >= 2 and intense):
        return "높음"
    if hits >= 1 or intense:
        return "중간"
    return "낮음"


def _estimate_suicide_signal(text: str) -> SuicideSignal:
    if _contains_any(text, SUICIDE_HIGH):
        return "높음"
    if _contains_any(text, SUICIDE_MID):
        return "중간"
    if "죽" in text and "싶" in text:
        return "낮음"
    return "없음"


def _estimate_risk_score(
    distress: DistressLevel,
    suicide_signal: SuicideSignal,
) -> int:
    score = 10
    if distress == "중간":
        score += 20
    if distress == "높음":
        score += 35
    if suicide_signal == "낮음":
        score += 20
    if suicide_signal == "중간":
        score += 45
    if suicide_signal == "높음":
        score += 70
    return min(score, 100)


def _next_action(risk_score: int) -> NextAction:
    if risk_score >= 80:
        return "즉시대응"
    if risk_score >= 60:
        return "전담자연계"
    if risk_score >= 35:
        return "주의환기"
    return "일반대화"


def _is_greeting(text: str) -> bool:
    return _contains_any(text, GREETING_CUES)


def _greeting_reply(greet_count: int) -> str:
    variants = [
        "안녕! 반가워. 오늘 어떤 일 있었는지 편하게 말해줄래?",
        "안녕, 괜찮아. 지금 마음 상태가 어때? 한 단어로 말해줘도 돼.",
        "말하기 어렵다면 '힘들어'처럼 한마디로 시작해도 괜찮아.",
        "오늘 있었던 일 중 하나만 골라서 말해줘도 좋아.",
        "지금 가장 신경 쓰이는 게 뭐야? 짧게 말해줘도 돼.",
        "내가 들어줄게. 오늘 마음이 어떤지부터 알려줄래?",
    ]
    index = max(greet_count - 1, 0) % len(variants)
    return variants[index]


def _compose_reply(
    history: List[ChatTurn],
    message: str,
    distress: DistressLevel,
    suicide_signal: SuicideSignal,
    risk_score: int = 0,
) -> str:
    normalized = message.replace(" ", "")
    
    # 0. 이미 이름/전화번호를 말한 경우 (자살 신호 이후 단계)
    # 최근 AI가 이름/전화번호를 요청했고, 이번 메시지에서 이름/전화번호를 준 경우 → 마무리 멘트
    recent_ai_for_contact = [turn.content for turn in history[-3:] if turn.role == "ai"]
    has_asked_contact_info_global = any(
        ("이름" in text) or ("전화번호" in text) or ("연락처" in text) or ("전화해줄까" in text)
        for text in recent_ai_for_contact
    )
    if has_asked_contact_info_global:
        # 전화번호 패턴: 숫자 10-11자리 (010-1234-5678, 01012345678, 1234567890 등)
        phone_pattern_global = r"\d{10,11}"
        has_phone_number_global = bool(re.search(phone_pattern_global, message))
        # 이름 패턴: 한글 2-4자 또는 영문 2-10자
        name_pattern_global = r"[가-힣]{2,4}|[a-zA-Z]{2,10}"
        has_name_global = bool(re.search(name_pattern_global, message))
        if has_phone_number_global or has_name_global:
            return (
                "알겠어. 조금만 기다려줘. 지금 바로 연락을 취해볼게. "
                "너 편이야, 혼자 버티지 말고 도움을 받아야 해. 곧 연락이 갈 거야."
            )
    
    # ⚠️ 매우 중요: 자살 신호가 있으면 즉시 적극적으로 대응 (최우선 처리)
    if suicide_signal in ("중간", "높음") or _contains_any(normalized, SUICIDE_HIGH) or _contains_any(normalized, SUICIDE_MID):
        # 연결 제안을 했는지 확인
        recent_ai = [turn.content for turn in history[-4:] if turn.role == "ai"]
        has_offered_connection = any(
            "연결" in text or "연락" in text or "괜찮을까" in text or "도와줄까" in text or "전화해줄까" in text
            for text in recent_ai
        )
        
        # 이름/전화번호 요청을 했는지 확인
        has_asked_contact_info = any(
            "이름" in text or "전화번호" in text or "연락처" in text
            for text in recent_ai
        )
        
        # 이름과 전화번호 제공 여부 확인
        # 전화번호 패턴: 숫자 10-11자리 (010-1234-5678, 01012345678, 1234567890 등)
        phone_pattern = r'\d{10,11}'  # 10-11자리 숫자
        has_phone_number = bool(re.search(phone_pattern, message))
        
        # 이름 패턴: 한글 2-4자 또는 영문 2-10자
        name_pattern = r'[가-힣]{2,4}|[a-zA-Z]{2,10}'
        has_name = bool(re.search(name_pattern, message))
        
        # 이름과 전화번호를 모두 제공했는지 확인
        if has_asked_contact_info and (has_phone_number or has_name):
            # 이름과 전화번호를 받았으면 마무리
            return "알겠어. 조금만 기다려줘. 지금 바로 연락을 취할게. 너 편이야, 혼자 버티지 말고 도움을 받아야 해. 곧 연락이 갈 거야."
        
        # 동의 응답 확인
        normalized_lower = normalized.lower()
        has_agreement = any(word in normalized_lower for word in ["응", "네", "좋아", "괜찮아", "그래", "해줘", "도와줘"])
        has_refusal = any(word in normalized for word in SHORT_NEGATIVE_RESPONSES) or any(
            word in normalized_lower for word in ["싫어", "안돼", "괜찮아", "아니", "거절", "원하지"]
        )
        
        if has_offered_connection and has_refusal:
            return (
                "알겠어. 지금 바로 연결하는 건 부담스러울 수 있지. 억지로 안 할게. "
                "그럼 지금은 여기서 얘기만 해도 괜찮아. "
                "조금이라도 편해지도록 같이 정리해보자. 지금 가장 힘든 순간이 언제였는지 말해줄래?"
            )
        
        if has_agreement and has_offered_connection:
            # 동의했으면 이름과 전화번호 요청
            return "알겠어. 조금만 기다려줘. 대신 전화해줄게. 이름하고 전화번호 알려줄래?"
        
        # 자살 신호가 있으면 즉시 전화번호 제공 및 대신 전화 제안
        return (
            "지금 많이 힘들어 보인다. 혼자 버티지 말고 즉시 도움을 받아야 해. "
            "112(응급)이나 1388 청소년 상담전화(24시간 무료)에 전화할 수 있어. "
            "내가 대신 전화해줄까? 이름하고 전화번호 알려줄래?"
        )
    
    # 비위기 종료 요청 처리 (친구 톤, 요약/감사/다시 와도 됨)
    if _is_end_request(message, len(history)) and suicide_signal in ("없음", "낮음"):
        recent_ai = [turn.content for turn in history[-3:] if turn.role == "ai"]
        closing_candidates = [
            "오늘 얘기해줘서 고마워. 필요하면 언제든 다시 와줘. 난 여기 있을게.",
            "여기까지 할게. 지금 마음이 조금이라도 가벼워졌으면 좋겠다. 언제든 또 얘기하자.",
            "응, 여기서 마칠게. 고마워. 다음에 또 마음 풀고 싶을 때 와줘.",
        ]
        return _pick_non_repeating(closing_candidates, recent_ai)

    if _is_greeting(normalized):
        recent_user = [turn.content for turn in history[-4:] if turn.role == "user"]
        greet_count = sum(1 for text in recent_user if _is_greeting(text.replace(" ", "")))
        return _greeting_reply(greet_count)
    # 학교폭력/괴롭힘 키워드 감지 시
    if _contains_any(normalized, BULLYING_CUES):
        # 히스토리 확인하여 이미 구체적 상황을 말했는지 확인
        recent_user = [turn.content for turn in history[-5:] if turn.role == "user"]
        recent_ai = [turn.content for turn in history[-3:] if turn.role == "ai"]
        recent_user_text = " ".join(recent_user).lower()
        has_frequency = any(word in recent_user_text for word in ["매일", "자주", "계속", "항상", "맨날"])
        has_safety_answer = any(word in recent_user_text for word in ["안전", "괜찮", "집", "학교", "교실"])
        asked_frequency_recently = _recent_ai_has_any(
            recent_ai, ["얼마나 자주", "매일", "자주", "계속", "항상", "맨날"]
        )
        asked_safety_recently = _recent_ai_has_any(
            recent_ai, ["안전", "괜찮은 곳", "지금은 괜찮"]
        )
        
        # 이미 구체적 상황을 말했는지 확인 (맞았다, 때렸다, 괴롭혔다 등)
        has_specific_violence = any(word in recent_user_text for word in [
            "맞았", "때렸", "때려", "괴롭혔", "괴롭혀", "때린", "맞아", "때려서", "맞아서"
        ])
        
        # 이미 같은 질문을 했는지 확인
        has_asked_situation = any(
            "어떤 상황" in text or "조금만 더 말해줄래" in text or "어떤 일이 있었는지" in text
            for text in recent_ai
        )
        
        # 연결 제안을 했는지 확인
        has_offered_connection = any(
            "연결" in text or "연락" in text or "괜찮을까" in text or "도와줄까" in text
            for text in recent_ai
        )
        
        # 동의 응답 확인 ("응", "네", "좋아", "괜찮아" 등)
        has_agreement = any(word in normalized.lower() for word in ["응", "네", "좋아", "괜찮아", "그래", "해줘", "도와줘"])
        
        # 이름/전화번호 요청을 했는지 확인
        has_asked_contact_info = any(
            "이름" in text or "전화번호" in text or "연락처" in text
            for text in recent_ai
        )
        
        if has_asked_contact_info:
            # 이름과 전화번호를 받았으면 마무리
            return "알겠어. 조금만 기다려줘. 곧 연락이 갈 거야. 너 편이야, 혼자 버티지 말고 도움을 받아야 해."
        
        if has_agreement and has_offered_connection:
            # 동의했으면 이름과 전화번호 요청
            return "알겠어. 조금만 기다려줘. 대신 전화해줄게. 이름하고 전화번호 알려줄래?"
        
        # 대화 턴 수 확인 (충분히 대화를 나눈 후에만 연결 제안)
        conversation_turns = len(history)
        
        if has_specific_violence:
            # 이미 구체적 상황을 말했으면 위로 메시지
            # 위험 점수가 높고 충분히 대화를 나눈 후에만 연결 제안
            if conversation_turns >= 4 and risk_score >= 60 and not has_offered_connection:
                candidates = [
                    "그런 일을 겪었다니 정말 무서웠고 힘들었을 것 같아. 혼자 버티지 말고 도움을 받아야 해. "
                    "선생님이나 부모님께 말씀드리는 것도 방법이야. 내가 연결 시켜줘도 괜찮을까?",
                    "그 얘기 들으니 걱정돼. 너 혼자 버티게 하고 싶지 않아. "
                    "선생님이나 부모님에게 같이 말해볼까? 내가 도와줘도 될까?",
                ]
                return _pick_non_repeating(candidates, recent_ai)
            else:
                candidates = [
                    "그런 일을 겪었다니 정말 무서웠고 힘들었을 것 같아. 혼자 버티지 말고 도움을 받아야 해. "
                    "선생님이나 부모님께 말씀드리는 것도 방법이야. 너 편이야, 같이 방법을 찾아보자.",
                    "네가 겪는 게 너무 힘들어 보여. 혼자 버티지 않아도 돼. "
                    "믿을 수 있는 어른에게 이야기하는 것도 방법이야. 나는 네 편이야.",
                ]
                return _pick_non_repeating(candidates, recent_ai)
        elif has_asked_situation:
            # 이미 물어봤는데 구체적 답변이 없으면 위로
            candidates = [
                "말하기 어려운 일이구나. 그런 일을 겪었다니 정말 힘들었을 것 같아. "
                "혼자 버티지 말고 도움을 받아야 해. 선생님이나 부모님께도 말씀드릴 수 있어. 너 편이야.",
                "쉽게 말하기 힘든 거 알아. 그래도 너 혼자 두고 싶지 않아. "
                "믿을 만한 어른에게 얘기할 수 있을까? 나는 네 편이야.",
            ]
            return _pick_non_repeating(candidates, recent_ai)
        else:
            # 처음 물어보는 경우
            if has_frequency and not asked_frequency_recently:
                candidates = [
                    "매일 그런 일이 있다면 정말 힘들었겠다. 지금은 안전한 곳에 있어? "
                    "요즘 특히 제일 힘든 순간이 언제였는지 말해줄래?",
                    "매일 겪는다는 말이 너무 마음 아프다. 지금은 괜찮은 장소에 있어? "
                    "도움받을 수 있는 어른이 떠오르는지 이야기해줄래?",
                ]
            elif has_frequency and asked_frequency_recently:
                candidates = [
                    "매일 겪는다는 말이 너무 마음 아파. 지금 네가 제일 힘든 순간이 언제인지 말해줄래?",
                    "매일이라고 하니까 더 걱정돼. 오늘 있었던 일 중에 가장 힘들었던 순간 하나만 말해줄래?",
                ]
            else:
                candidates = [
                    "그런 일을 겪었다니 많이 힘들었겠다. 지금은 안전한 곳에 있어? "
                    "어떤 상황이었는지 조금만 더 말해줄래?",
                    "그 얘기 들으니 마음이 아프다. 지금은 안전한 곳이야? "
                    "어떤 일이 있었는지 편하게 말해줄래?",
                ]
            # 안전 질문을 이미 했으면 안전 관련 문장은 피한다.
            if asked_safety_recently:
                candidates = [c for c in candidates if "안전" not in c]
            return _pick_non_repeating(candidates, recent_ai)
    # 자살 신호가 있으면 이미 위에서 처리했으므로 여기서는 중복 처리 방지
    # (이 부분은 suicide_signal이 "낮음"이거나 히스토리에만 있는 경우를 처리)
    
    # 자살 신호가 히스토리에 있고, 현재 메시지에서 부정적 인식을 표현하는 경우
    recent_user_all = [turn.content for turn in history[-5:] if turn.role == "user"]
    recent_user_text = " ".join(recent_user_all).lower()
    current_message_lower = normalized.lower()
    
    # 히스토리에 자살 신호가 있고, 현재 메시지에서 부정적 인식을 표현하는지 확인
    has_suicide_in_history = any(word in recent_user_text for word in ["자살", "죽고", "죽을", "끝내", "살고 싶지"])
    has_negative_belief_now = any(phrase in current_message_lower for phrase in [
        "경찰", "어른", "도와줄", "없", "못", "아무것도", "소용없", "할 수 있는"
    ])
    
    if has_suicide_in_history and has_negative_belief_now:
        return (
            "아니야, 경찰이랑 어른들이 무조건 도와줄 거야. 너를 지켜줄 사람들이 있어. "
            "1388 청소년 상담전화(24시간 무료)나 112(응급)에 전화해볼 수 있어. "
            "선생님이나 부모님께도 말씀드릴 수 있어. 너 편이야, 혼자 버티지 말고 같이 방법을 찾아보자."
        )
    if distress == "높음":
        # 최근 사용자 발화 가져오기 (미러링용)
        last_user = None
        for turn in reversed(history):
            if turn.role == "user":
                last_user = turn.content
                break
        # 최근 AI 응답들 (반복 방지용)
        recent_ai = [turn.content for turn in history[-3:] if turn.role == "ai"]
        base_reply_1 = (
            f"{last_user} 라고 말해준 거 보니까 정말 많이 힘들었겠다는 생각이 들어. "
            "지금 네가 버티고 있는 상황이 어떤지, 조금만 더 얘기해줄 수 있어? 내가 네 편에서 같이 들어줄게."
        ) if last_user else (
            "지금 많이 힘들다는 게 느껴져. 어떤 상황인지 조금만 더 얘기해줄 수 있어? 내가 네 편에서 같이 들어줄게."
        )
        base_reply_2 = (
            f"{last_user} 라고 느낄 만큼 진짜 많이 힘들었겠다. "
            "요즘 특히 언제가 제일 괴롭다고 느껴져? 친구한테 털어놓는다고 생각하고 편하게 말해줘."
        ) if last_user else (
            "요즘 특히 언제가 제일 괴롭다고 느껴져? 친구한테 털어놓는다고 생각하고 편하게 말해줘."
        )
        # 최근에 같은 질문(상황 설명 요청)을 했으면 다른 방향으로 전환
        if _recent_ai_has_any(recent_ai, ["어떤 상황", "조금만 더 얘기", "어떤 일이 있었는지"]):
            alt_candidates = [
                "지금 가장 힘든 순간이 언제인지 하나만 말해줄래? 내가 네 편이야.",
                "오늘 있었던 일 중에 제일 괴로웠던 장면 하나만 알려줄래? 같이 정리해보자.",
            ]
            return _pick_non_repeating(alt_candidates, recent_ai)
        # 바로 전에 같은 문장을 썼다면 다른 버전 사용
        if recent_ai and recent_ai[-1] == base_reply_1:
            return base_reply_2
        if recent_ai and recent_ai[-1] == base_reply_2:
            return base_reply_1
        # 기본은 첫 번째 버전
        return base_reply_1
    if distress == "중간":
        # 대화 히스토리 확인하여 반복 방지
        recent_user = [turn.content for turn in history[-4:] if turn.role == "user"]
        recent_ai = [turn.content for turn in history[-4:] if turn.role == "ai"]
        
        # 이미 구체적 상황을 말했는지 확인
        has_specific_situation = any(
            word in " ".join(recent_user) 
            for word in ["때려", "괴롭", "폭력", "왕따", "따돌", "때린", "괴롭혀"]
        )
        
        # 이미 같은 질문을 했는지 확인
        has_asked_situation = _recent_ai_has_any(
            recent_ai, ["어떤 상황", "어떤 일이", "조금 더 말해줄래", "힘들었는지"]
        )
        asked_frequency_recently = _recent_ai_has_any(
            recent_ai, ["얼마나 자주", "매일", "자주", "계속", "항상", "맨날"]
        )
        asked_safety_recently = _recent_ai_has_any(
            recent_ai, ["안전", "괜찮은 곳", "지금은 괜찮"]
        )
        is_short_negative = any(word in normalized for word in SHORT_NEGATIVE_RESPONSES)
        
        if has_specific_situation and not has_asked_situation:
            # 구체적 상황을 말했고 아직 안 물어봤으면 안전/빈도 확인
            candidates = [
                "그런 일을 겪었다니 정말 힘들었을 것 같아. 지금은 안전한 곳에 있어? 얼마나 자주 일어나는 일이야?",
                "그 얘기 들으니 마음이 아프다. 지금은 괜찮은 곳이야? 요즘 얼마나 자주 있어?",
            ]
            if asked_safety_recently:
                candidates = [c for c in candidates if "안전" not in c]
            if asked_frequency_recently:
                candidates = [c for c in candidates if "얼마나 자주" not in c and "요즘 얼마나 자주" not in c]
            return _pick_non_repeating(candidates, recent_ai)
        elif has_specific_situation:
            # 이미 물어봤으면 다음 단계로 이동
            candidates = [
                "그런 일을 겪었다니 정말 무서웠을 것 같아. 선생님이나 부모님께 말해본 적 있어? 혼자 버티지 말고 같이 방법을 찾아보자.",
                "혼자 버티는 게 너무 힘들었겠다. 믿을 수 있는 어른에게 얘기해본 적 있어? 내가 같이 방법을 찾아줄게.",
            ]
            return _pick_non_repeating(candidates, recent_ai)
        elif is_short_negative:
            # 짧은 부정 응답이 반복될 때는 같은 질문을 피함
            candidates = [
                "괜찮아, 지금 말하기 어렵다면 괜찮아. 그럼 지금 당장 필요한 게 뭔지 하나만 말해줄래?",
                "말하기 힘든 거 이해해. 그럼 오늘은 어떤 도움을 받고 싶은지부터 말해줄래?",
            ]
            return _pick_non_repeating(candidates, recent_ai)
        else:
            # 아직 구체적 상황을 안 말했으면 구체적으로 물어보기
            candidates = [
                "그랬구나, 정말 힘들었겠어. 어떤 일이 있었는지 조금 더 말해줄래?",
                "그 말이 마음에 남아. 오늘 있었던 일 중에 제일 힘들었던 순간을 하나만 알려줄래?",
            ]
            return _pick_non_repeating(candidates, recent_ai)
    
    # 포기/부정적 발언 감지 (학교폭력 상황에서 포기하려고 할 때)
    recent_user_all = [turn.content for turn in history[-5:] if turn.role == "user"]
    recent_user_text = " ".join(recent_user_all).lower()
    current_message_lower = normalized.lower()
    
    # 학교폭력 상황이 히스토리에 있고, 포기하려고 하는지 확인
    has_bullying_in_history = any(word in recent_user_text for word in [
        "괴롭", "때려", "맞았", "폭력", "왕따", "따돌", "괴롭혀"
    ])
    has_giving_up = any(phrase in current_message_lower for phrase in GIVING_UP_CUES)
    
    if has_bullying_in_history and has_giving_up:
        # 학교폭력 상황에서 포기하려고 할 때 적극적으로 권유
        return (
            "아니야, 그렇게 참고 지내면 안 돼. 그런 일을 겪고 있는데 혼자 버티면 더 힘들어질 수 있어. "
            "부모님이나 선생님께 꼭 말씀드려야 해. 1388 청소년 상담전화(24시간 무료)에 전화해서 도움을 받을 수도 있어. "
            "혼자 해결하려고 하지 말고 어른들의 도움을 받는 게 중요해. 너 편이야, 같이 방법을 찾아보자."
        )
    
    # 짧은 부정적 답변 반복 감지 ("싫어", "없어" 등)
    recent_user = [turn.content for turn in history[-5:] if turn.role == "user"]
    recent_ai = [turn.content for turn in history[-3:] if turn.role == "ai"]
    
    # 최근 3턴 이상 짧은 부정적 답변이 반복되는지 확인
    short_negative_count = sum(1 for text in recent_user[-3:] if text.strip() in SHORT_NEGATIVE_RESPONSES)
    has_repeated_short_negative = short_negative_count >= 2
    
    # 이전 응답과 같은 패턴인지 확인
    has_generic_response = any(
        phrase in " ".join(recent_ai) 
        for phrase in ["알려줘서 고마워", "괜찮아 천천히", "편하게 얘기해줘", "어떤 일이 있었는지", "어떤 기분인지"]
    )
    
    # 학생이 구체적인 내용을 말했는지 확인
    has_specific_content = any(
        word in " ".join(recent_user) 
        for word in ["때려", "괴롭", "폭력", "왕따", "힘들어", "불안", "피곤", "지쳤", "얘기하고 싶어", "학교"]
    )
    
    # 짧은 부정적 답변이 반복되는 경우
    if has_repeated_short_negative:
        if has_specific_content:
            # 이미 구체적 내용을 말했으면 위로와 도움 방법 제시
            return (
                "말하기 어려운 일이구나. 하지만 혼자 버티지 말고 도움을 받을 수 있어. "
                "1388 청소년 상담전화(24시간 무료)나 112(응급)에 전화해볼 수 있어. "
                "선생님이나 부모님께도 말씀드릴 수 있어. 너 편이야."
            )
        else:
            # 아직 구체적 내용을 안 말했으면 다른 방식으로 접근
            return "괜찮아, 말하기 어려울 수 있어. 한 단어로만 말해도 돼. 힘들어? 불안해? 피곤해?"
    
    # 짧은 답변('없어', '몰라' 등)에 대한 처리
    if any(len(text) < 5 and text not in ["안녕", "고마워", "?"] for text in recent_user[-2:]):
        # 이미 알고 있는 정보를 바탕으로 응답
        has_violence = any(word in " ".join(recent_user) for word in ["때려", "괴롭", "폭력", "왕따"])
        if has_violence:
            return "그렇구나. 그럼 지금 상황이 얼마나 심각한지, 어떻게 하고 싶은지 같이 생각해볼까? 혼자 버티지 말고 같이 방법을 찾아보자."
        elif has_specific_content:
            # 구체적 내용을 말했으면 그에 맞게 응답
            return "그랬구나. 더 자세히 얘기해줄래? 어떤 기분이 드는지, 어떤 일이 있었는지 편하게 말해줘."
        else:
            # 일반적이지만 이전과 다른 방식 (반복 방지)
            if has_generic_response:
                return "괜찮아, 말하기 어려울 수 있어. 한 단어로만 말해도 돼. 힘들어? 불안해? 피곤해?"
            else:
                return "괜찮아, 천천히 말해도 돼. 어떤 기분이 드는지 편하게 얘기해줘."
    
    # 일반 응답 (이미 구체적 상황을 말한 후에는 사용하지 않음)
    if has_specific_content:
        if has_generic_response:
            return "그랬구나. 더 자세히 얘기해줄래? 어떤 일이 있었는지, 어떤 기분인지 편하게 말해줘."
        else:
            return "그랬구나. 더 말하고 싶은 게 있으면 편하게 얘기해줘."
    
    # 최후의 수단 (반복 방지)
    if has_generic_response:
        return "괜찮아, 말하기 어려울 수 있어. 한 단어로만 말해도 돼. 힘들어? 불안해? 피곤해?"
    
    return "알려줘서 고마워. 지금 필요한 게 있으면 편하게 말해줘."


def _extract_key_topics(history: List[ChatTurn]) -> List[str]:
    """대화에서 주요 주제 추출"""
    topics = []
    user_messages = [turn.content for turn in history if turn.role == "user"]
    text = " ".join(user_messages)
    
    # 키워드 기반 주제 추출
    if any(word in text for word in ["괴롭", "따돌", "폭력", "때렸"]):
        topics.append("학교폭력/또래관계")
    if any(word in text for word in ["가족", "부모", "집"]):
        topics.append("가정 문제")
    if any(word in text for word in ["성적", "공부", "시험", "학업"]):
        topics.append("학업 스트레스")
    if any(word in text for word in ["우울", "외로", "불안"]):
        topics.append("정서적 어려움")
    if any(word in text for word in ["죽", "자살", "끝내"]):
        topics.append("자살 사고")
    
    return topics if topics else ["일반 상담"]


def _build_end_report(
    history: List[ChatTurn],
    risk_score: int,
    distress: DistressLevel,
    suicide_signal: SuicideSignal,
) -> EndReport:
    """종합 결과 생성 - 더 상세한 정보 포함"""
    # 대화 요약 생성
    user_messages = [turn.content for turn in history if turn.role == "user"]
    if len(user_messages) >= 3:
        summary = f"주요 고민: {user_messages[0]} → {user_messages[-1]}"
    else:
        summary = " / ".join(user_messages) if user_messages else "대화 요약 없음"
    
    # 상태 추이 판단
    if risk_score >= 80:
        trend = "위험"
    elif risk_score >= 60:
        trend = "주의 필요"
    elif distress == "낮음" and risk_score < 35:
        trend = "안정화 중"
    else:
        trend = "관찰 필요"
    
    # 다음 가이드 생성
    if risk_score >= 80:
        next_guidance = "즉시 전문가 상담이 필요합니다. 1388 청소년 상담전화 또는 응급실을 방문하세요."
    elif risk_score >= 60:
        next_guidance = "전문 상담사나 신뢰할 수 있는 어른과 상담하는 것을 권장합니다."
    elif distress != "낮음":
        next_guidance = "다음 대화에서는 구체적인 상황과 감정을 더 자세히 나눠보면 좋겠어요."
    else:
        next_guidance = "긍정적인 루틴을 유지하고, 필요할 때 언제든 다시 대화해요."
    
    # 주요 주제 추출
    key_topics = _extract_key_topics(history)
    
    return EndReport(
        summary=summary,
        risk_score=risk_score,
        trend=trend,
        next_guidance=next_guidance,
        distress_level=distress,
        suicide_signal=suicide_signal,
        conversation_turns=len(history),
        key_topics=key_topics,
    )


def build_history_analysis(history: List[ChatTurn], current_message: str) -> List[TurnAnalysis]:
    """
    전체 대화를 훑으면서 각 사용자 발화/AI 응답에 대한 분석 리스트를 생성.
    - 위험도 계산은 해당 사용자 발화까지만의 텍스트를 기준으로 함.
    """
    analyses: List[TurnAnalysis] = []
    user_only_history: List[ChatTurn] = []

    # 기존 히스토리에 현재 사용자 메시지를 추가한 상태로 본다.
    extended_history = history + [ChatTurn(role="user", content=current_message)]

    for idx, turn in enumerate(extended_history):
        if turn.role != "user":
            continue

        # 이 사용자 메시지까지의 사용자 텍스트만 모아서 위험도 평가
        user_only_history.append(turn)
        user_text = "".join(t.content for t in user_only_history).replace(" ", "")

        d = _estimate_distress(user_text)
        s = _estimate_suicide_signal(user_text)
        r = _estimate_risk_score(d, s)
        a = _next_action(r)

        # 바로 다음 AI 응답(있다면) 연결
        ai_reply: Optional[str] = None
        for j in range(idx + 1, len(extended_history)):
            if extended_history[j].role == "ai":
                ai_reply = extended_history[j].content
                break

        analyses.append(
            TurnAnalysis(
                turn_index=idx,
                user_message=turn.content,
                ai_reply=ai_reply,
                emotional_distress=d,
                suicide_signal=s,
                risk_score=r,
                next_action=a,
            )
        )

    return analyses


def enrich_history_with_analysis(
    history: List[Dict],
    current_message: str,
    include_current: bool = True,
) -> List[Dict]:
    """
    history 딕셔너리 리스트를 받아서 각 사용자 메시지에 analysis 필드를 추가.
    - 위험도 계산은 해당 사용자 발화까지만의 텍스트를 기준으로 함.
    
    Args:
        history: 대화 히스토리 딕셔너리 리스트 (예: [{"role": "user", "content": "..."}, ...])
        current_message: 현재 사용자 메시지
    
    Returns:
        각 사용자 메시지에 analysis 필드가 추가된 history
    """
    try:
        enriched_history = []
        user_only_texts = []
        
        # 기존 히스토리 복사
        for item in history:
            enriched_history.append(item.copy())
        
        # 현재 메시지 추가 (이미 히스토리에 포함되어 있으면 생략)
        if include_current and current_message:
            enriched_history.append({"role": "user", "content": current_message})
        
        # 각 사용자 메시지에 대해 분석 수행
        for idx, item in enumerate(enriched_history):
            if item.get("role") != "user":
                continue
            
            # 이 사용자 메시지까지의 사용자 텍스트만 모아서 위험도 평가
            user_content = item.get("content", "")
            if not user_content:
                continue
                
            user_only_texts.append(user_content)
            user_text = "".join(user_only_texts).replace(" ", "")
            
            try:
                d = _estimate_distress(user_text)
                s = _estimate_suicide_signal(user_text)
                r = _estimate_risk_score(d, s)
                a = _next_action(r)
                
                # 해당 시점까지의 대화로 주제/턴 계산
                slice_history = [
                    ChatTurn(role=turn.get("role", "user"), content=turn.get("content", ""))
                    for turn in enriched_history[: idx + 1]
                ]
                key_topics = _extract_key_topics(slice_history)
                conversation_turns = len(slice_history)
                if r >= 80:
                    trend = "위험"
                elif r >= 60:
                    trend = "주의 필요"
                elif d == "낮음" and r < 35:
                    trend = "안정화 중"
                else:
                    trend = "관찰 필요"
                
                # 해당 사용자 메시지에 analysis 필드 추가 (Literal 타입은 문자열로 변환)
                item["analysis"] = {
                    "emotional_distress": str(d),
                    "distress_level": str(d),
                    "suicide_signal": str(s),
                    "risk_score": int(r),
                    "next_action": str(a),
                    "trend": trend,
                    "conversation_turns": conversation_turns,
                    "key_topics": key_topics,
                }
            except Exception as e:
                print(f"⚠️ 분석 실패 (idx={idx}, content={user_content[:50]}): {e}")
                import traceback
                traceback.print_exc()
                # 기본값으로 설정
                item["analysis"] = {
                    "emotional_distress": "낮음",
                    "suicide_signal": "없음",
                    "risk_score": 10,
                    "next_action": "일반대화",
                }
        
        return enriched_history
    except Exception as e:
        print(f"⚠️ enrich_history_with_analysis 전체 실패: {e}")
        import traceback
        traceback.print_exc()
        # 기본 히스토리 반환
        result = history.copy()
        result.append({"role": "user", "content": current_message})
        return result


def analyze_message(history: List[ChatTurn], message: str) -> Analysis:
    """
    현재 메시지에 대한 분석이지만,
    위험 점수와 자살 신호는 전체 대화(사용자 발화 기준)를 고려하여 계산.
    이렇게 해야 마지막에 전화번호만 보내도 이전 자살 신호가 유지됨.
    """
    # 전체 사용자 메시지 + 현재 메시지를 합쳐서 위험도 평가
    user_texts = [turn.content for turn in history if turn.role == "user"]
    full_text = "".join(user_texts + [message]).replace(" ", "")

    distress = _estimate_distress(full_text)
    suicide_signal = _estimate_suicide_signal(full_text)
    risk_score = _estimate_risk_score(distress, suicide_signal)
    
    # 위험 점수가 높거나 자살 신호가 있을 때만 연결 제안을 고려
    # _compose_reply에서 위험 점수 정보도 필요하므로 전달
    reply = _compose_reply(history, message, distress, suicide_signal, risk_score)
    action = _next_action(risk_score)
    return Analysis(
        emotional_distress=distress,
        suicide_signal=suicide_signal,
        risk_score=risk_score,
        next_action=action,
        reply=reply,
    )


def should_end_conversation(
    history: List[ChatTurn],
    risk_score: int,
    distress: DistressLevel,
    message: str,
) -> bool:
    """
    대화 종료 조건:
    - 사용자가 명시적으로 종료를 요청한 경우에만 종료
    - 위험 점수가 높아도 자동으로 종료하지 않음 (대화를 계속 이어가야 함)
    """
    # 0. 자살 위기 상황에서 이름/전화번호를 이미 제공한 경우 → 대화 종료
    recent_ai_for_contact = [turn.content for turn in history[-3:] if turn.role == "ai"]
    has_asked_contact_info_global = any(
        ("이름" in text) or ("전화번호" in text) or ("연락처" in text) or ("전화해줄까" in text)
        for text in recent_ai_for_contact
    )
    if has_asked_contact_info_global:
        # 전화번호 패턴: 숫자 10-11자리
        import re
        phone_pattern_global = r"\d{10,11}"
        has_phone_number_global = bool(re.search(phone_pattern_global, message))
        # 이름 패턴: 한글 2-4자 또는 영문 2-10자
        name_pattern_global = r"[가-힣]{2,4}|[a-zA-Z]{2,10}"
        has_name_global = bool(re.search(name_pattern_global, message))
        if has_phone_number_global or has_name_global:
            return True

    # 1. 명시적 종료 요청만 감지 (인사말 "안녕"은 제외)
    # "안녕"은 대화 시작 인사일 수 있으므로 종료 키워드에서 제외
    if _is_end_request(message, len(history)):
        return True
    
    # 위험 점수가 높아도 자동으로 종료하지 않음
    # 대화를 계속 이어가서 도움을 제공해야 함
    return False


def build_report(
    history: List[ChatTurn],
    risk_score: int,
    distress: DistressLevel,
    suicide_signal: SuicideSignal,
) -> EndReport:
    return _build_end_report(history, risk_score, distress, suicide_signal)
