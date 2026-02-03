from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .agent import analyze_message, should_end_conversation, build_report, build_history_analysis, enrich_history_with_analysis
from .llm import generate_reply
from .schemas import ChatRequest, ChatResponse, TurnAnalysis
from .storage import save_conversation, list_conversations, get_conversation

# RAG는 선택적으로 로드
try:
    from .rag import get_db_info
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    def get_db_info():
        return {"path": "N/A", "collection": "N/A", "chunk_count": 0, "exists": False}


load_dotenv()

app = FastAPI(title="Emotion Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/rag/info")
def rag_info() -> dict:
    """RAG DB 정보 확인"""
    return get_db_info()


@app.get("/api/admin/conversations")
def get_conversations_list(include_test: bool = False) -> dict:
    """관리자: 저장된 대화 목록 조회"""
    conversations = list_conversations(include_test=include_test)
    return {"conversations": conversations}


@app.get("/api/admin/conversations/{filename}")
def get_conversation_detail(filename: str, is_test: bool = False) -> dict:
    """관리자: 특정 대화 상세 조회"""
    conversation = get_conversation(filename, is_test=is_test)
    if not conversation:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
    return conversation


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    import traceback
    from fastapi import HTTPException
    from .schemas import DistressLevel, SuicideSignal, NextAction
    
    try:
        print("[REQ] chat request received")
        # 1. 기본 분석 수행 (에러 발생 시 기본값 사용)
        try:
            analysis = analyze_message(payload.history, payload.message)
        except Exception as analysis_error:
            print("[WARN] analysis failed")
            # 기본 분석 객체 생성
            from .agent import Analysis
            from .schemas import DistressLevel, SuicideSignal, NextAction
            analysis = Analysis(
                emotional_distress="낮음",
                suicide_signal="없음",
                risk_score=10,
                next_action="일반대화",
                reply="죄송해요, 잠시 문제가 생겼어요. 다시 말해줄 수 있을까?",
            )
        
        # 2. LLM 응답 시도 (실패해도 계속 진행)
        llm_reply = None
        try:
            llm_reply = generate_reply(payload.history, payload.message)
        except Exception as llm_error:
            print("[WARN] LLM call failed, using fallback reply")
        
        # 3. 응답 선택 로직
        # ⚠️ 자살 신호가 있거나(중간/높음) 자살 관련 키워드가 포함된 경우에는
        #    규칙 기반 응답(analysis.reply)을 최우선으로 사용하고, LLM 응답은 무시한다.
        import re
        suicide_keywords = ["자살", "죽고 싶", "죽고싶", "죽고싶어", "죽을래", "끝내고 싶", "끝내고싶", "살고 싶지", "살고싶지"]
        msg_no_space = payload.message.replace(" ", "")
        has_suicide_keyword = any(k.replace(" ", "") in msg_no_space for k in suicide_keywords)
        
        # 히스토리에 자살 신호가 있는지 확인
        recent_user_messages = [turn.content for turn in payload.history[-5:] if turn.role == "user"]
        recent_user_text = " ".join(recent_user_messages).lower()
        has_suicide_in_history = any(word in recent_user_text for word in ["자살", "죽고", "죽을", "끝내", "살고 싶지"])
        
        # 이름/전화번호 제공 여부 확인
        phone_pattern = r'\d{10,11}'  # 10-11자리 숫자
        has_phone_number = bool(re.search(phone_pattern, payload.message))
        name_pattern = r'[가-힣]{2,4}|[a-zA-Z]{2,10}'  # 한글 2-4자 또는 영문 2-10자
        has_name = bool(re.search(name_pattern, payload.message))
        
        # 이전 AI 응답에서 이름/전화번호 요청 여부 확인
        recent_ai_messages = [turn.content for turn in payload.history[-3:] if turn.role == "ai"]
        has_asked_contact_info = any(
            "이름" in text or "전화번호" in text or "연락처" in text or "전화해줄까" in text
            for text in recent_ai_messages
        )
        
        # 이름/전화번호를 제공한 경우 무조건 규칙 응답 우선 (마무리 메시지)
        if has_asked_contact_info and (has_phone_number or has_name):
            reply = analysis.reply
        # 자살 신호가 있으면(현재 메시지 또는 히스토리) 규칙 응답 우선
        elif analysis.suicide_signal in ("중간", "높음") or has_suicide_keyword or has_suicide_in_history:
            reply = analysis.reply
        else:
            # 그 외의 경우에는 LLM 응답이 있으면 우선 사용
            reply = llm_reply if llm_reply else analysis.reply
        
        # 대화 종료 여부 확인
        try:
            conversation_end = should_end_conversation(
                payload.history,
                analysis.risk_score,
                analysis.emotional_distress,
                payload.message,
            )
        except Exception as end_error:
            print(f"⚠️ 대화 종료 확인 실패: {end_error}")
            conversation_end = False

        # 전체 대화에 대한 턴별 분석 생성 (JSON 출력용)
        # 응답 시에는 None으로 설정 (저장 시에만 사용)
        history_analysis = None
        # try:
        #     history_analysis = build_history_analysis(payload.history, payload.message)
        # except Exception as history_error:
        #     print(f"⚠️ 히스토리 분석 생성 실패: {history_error}")
        #     traceback.print_exc()
        
        end_report = None
        if conversation_end:
            try:
                end_report = build_report(
                    payload.history,
                    analysis.risk_score,
                    analysis.emotional_distress,
                    analysis.suicide_signal,
                )
            except Exception as report_error:
                print("[WARN] end report build failed")
                end_report = None

        # 모든 사용자 발화마다 저장 (요청 단위 저장)
        try:
            base_history = [
                {"role": turn.role, "content": turn.content}
                for turn in payload.history
            ]
            # 연속 중복 발화 제거 (같은 role/content가 연속으로 들어오는 경우)
            deduped_history = []
            for item in base_history:
                if not deduped_history:
                    deduped_history.append(item)
                    continue
                last = deduped_history[-1]
                if last["role"] == item["role"] and last["content"] == item["content"]:
                    continue
                deduped_history.append(item)
            # 현재 메시지가 이미 히스토리에 포함되어 있으면 중복 추가하지 않음
            has_current_in_history = (
                bool(deduped_history)
                and deduped_history[-1]["role"] == "user"
                and deduped_history[-1]["content"] == payload.message
            )
            # 각 사용자 메시지에 분석 포함
            final_history = enrich_history_with_analysis(
                deduped_history,
                payload.message,
                include_current=not has_current_in_history,
            )
            # 마지막 AI 응답 추가
            final_history.append({"role": "ai", "content": reply})

            # 최종 히스토리 연속 중복 제거 (저장 직전 안전장치)
            deduped_final = []
            for item in final_history:
                if not deduped_final:
                    deduped_final.append(item)
                    continue
                last = deduped_final[-1]
                if last.get("role") == item.get("role") and last.get("content") == item.get("content"):
                    continue
                deduped_final.append(item)
            final_history = deduped_final

            # end_report를 딕셔너리로 변환 (Pydantic v1/v2 호환)
            try:
                end_report_dict = end_report.dict() if hasattr(end_report, 'dict') else end_report.model_dump()
            except Exception:
                end_report_dict = None

            save_conversation(
                history=final_history,
                analysis={
                    "emotional_distress": str(analysis.emotional_distress),
                    "suicide_signal": str(analysis.suicide_signal),
                    "risk_score": int(analysis.risk_score),
                    "next_action": str(analysis.next_action),
                },
                end_report=end_report_dict,
                is_test=payload.is_admin,  # 관리자 모드면 테스트로 저장
            )
        except Exception as save_error:
            print("[WARN] conversation save failed")
        
        # 안전하게 ChatResponse 생성
        try:
            return ChatResponse(
                reply=reply or "죄송해요, 잠시 문제가 생겼어요. 다시 말해줄 수 있을까?",
                emotional_distress=analysis.emotional_distress,
                suicide_signal=analysis.suicide_signal,
                risk_score=analysis.risk_score,
                next_action=analysis.next_action,
                conversation_end=conversation_end,
                end_report=end_report,
                history_analysis=history_analysis,
            )
        except Exception as response_error:
            print("[WARN] ChatResponse build failed")
            # 최소한의 응답이라도 반환
            return ChatResponse(
                reply="죄송해요, 잠시 문제가 생겼어요. 다시 말해줄 수 있을까?",
                emotional_distress="낮음",
                suicide_signal="없음",
                risk_score=10,
                next_action="일반대화",
                conversation_end=False,
                end_report=None,
                history_analysis=None,
            )
        
    except HTTPException:
        # HTTPException은 그대로 전달
        raise
    except Exception as e:
        # 예상치 못한 에러는 상세 정보와 함께 반환
        print("[ERR] chat API error")
        
        # 클라이언트에는 간단한 메시지만 전달하되, 로그에는 상세 정보 기록
        try:
            # 최소한의 응답이라도 반환 시도
            analysis = analyze_message(payload.history, payload.message)
            return ChatResponse(
                reply=analysis.reply,
                emotional_distress=analysis.emotional_distress,
                suicide_signal=analysis.suicide_signal,
                risk_score=analysis.risk_score,
                next_action=analysis.next_action,
                conversation_end=False,
                end_report=None
            )
        except Exception as fallback_error:
            print("[ERR] fallback failed")
            # 마지막 수단: 기본 응답
            return ChatResponse(
                reply="죄송해요, 잠시 문제가 생겼어요. 다시 말해줄 수 있을까?",
                emotional_distress="낮음",
                suicide_signal="없음",
                risk_score=0,
                next_action="일반대화",
                conversation_end=False,
                end_report=None
            )
