from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Literal, Optional


Role = Literal["user", "ai"]
DistressLevel = Literal["낮음", "중간", "높음"]
SuicideSignal = Literal["없음", "낮음", "중간", "높음"]
NextAction = Literal["일반대화", "주의환기", "전담자연계", "즉시대응"]


class ChatTurn(BaseModel):
    role: Role
    content: str


class ChatRequest(BaseModel):
    history: List[ChatTurn] = Field(default_factory=list)
    message: str
    is_admin: bool = False  # 관리자 모드 여부


class EndReport(BaseModel):
    summary: str = Field(..., description="대화 요약")
    risk_score: int = Field(..., description="최종 위험 점수")
    trend: str = Field(..., description="상태 추이 (안정화 중 / 주의 필요 / 위험)")
    next_guidance: str = Field(..., description="다음 대화 시 가이드")
    
    # 추가 정보
    distress_level: DistressLevel = Field(..., description="최종 정서적 고통 수준")
    suicide_signal: SuicideSignal = Field(..., description="최종 자살 신호")
    conversation_turns: int = Field(..., description="대화 턴 수")
    key_topics: List[str] = Field(default_factory=list, description="주요 주제")


class TurnAnalysis(BaseModel):
    """각 사용자 발화/AI 응답에 대한 분석 결과 (히스토리용)"""
    turn_index: int = Field(..., description="대화 순서 인덱스 (0부터 시작)")
    user_message: str = Field(..., description="사용자 메시지")
    ai_reply: Optional[str] = Field(None, description="해당 턴에 대한 AI 응답")
    emotional_distress: DistressLevel = Field(..., description="정서적 고통 상태")
    suicide_signal: SuicideSignal = Field(..., description="자살 신호")
    risk_score: int = Field(..., description="위험 점수 (0-100)")
    next_action: NextAction = Field(..., description="다음 조치")


class ChatResponse(BaseModel):
    # 학생에게 보여줄 답변
    reply: str = Field(..., description="AI 답변 내용")
    
    # 상태 정보 (시스템/관리자용)
    emotional_distress: DistressLevel = Field(..., description="정서적 고통 상태")
    suicide_signal: SuicideSignal = Field(..., description="자살 신호")
    risk_score: int = Field(..., description="위험 점수 (0-100)")
    next_action: NextAction = Field(..., description="다음 조치")
    
    # 대화 종료 관련
    conversation_end: bool = Field(..., description="대화 종료 여부")
    end_report: Optional[EndReport] = Field(None, description="대화 종료 시 종합 결과")

    # 히스토리 기반 분석 (선택적)
    history_analysis: Optional[List[TurnAnalysis]] = Field(
        None,
        description="각 사용자 발화/AI 응답에 대한 분석 결과 리스트"
    )
    
    # JSON 출력 시 한글 필드명으로 매핑
    class Config:
        json_schema_extra = {
            "example": {
                "답변": "많이 힘들었겠구나. 어떤 상황이었는지 조금 더 말해줄래?",
                "정서적 고통 상태": "높음",
                "자살 신호": "낮음",
                "위험 점수": 45,
                "다음 조치": "주의환기",
                "대화 종료": False,
                "종합 결과": None
            }
        }
