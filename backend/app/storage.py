"""
대화 저장 및 조회 모듈
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

STORAGE_DIR = Path("data/conversations")
TEST_STORAGE_DIR = Path("data/conversations/test")


def ensure_storage_dir(is_test: bool = False):
    """저장 디렉토리 생성"""
    if is_test:
        TEST_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    else:
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def save_conversation(
    history: List[Dict],
    analysis: Dict,
    end_report: Optional[Dict] = None,
    is_test: bool = False,
) -> str:
    """
    대화를 JSON 파일로 저장
    
    Args:
        history: 대화 히스토리 (각 사용자 메시지에 analysis 필드 포함)
        analysis: 최종 분석 결과
        end_report: 종합 리포트 (선택)
        is_test: 테스트 대화 여부 (관리자 모드)
    
    Returns:
        저장된 파일명
    """
    ensure_storage_dir(is_test)
    
    # 파일명: 날짜_시간.json (테스트는 test_ 접두사 추가)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = "test_" if is_test else ""
    filename = f"{prefix}{timestamp}.json"
    
    # 저장 디렉토리 선택
    storage_dir = TEST_STORAGE_DIR if is_test else STORAGE_DIR
    filepath = storage_dir / filename
    
    # 저장할 데이터 구조
    conversation_data: Dict = {
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M:%S"),
        "history": history,  # 각 사용자 메시지에 analysis 필드가 포함됨
        "analysis": analysis,
        "end_report": end_report,
    }
    
    # JSON 파일로 저장
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(conversation_data, f, ensure_ascii=False, indent=2)
    
    return filename


def list_conversations(include_test: bool = False) -> List[Dict]:
    """
    저장된 모든 대화 목록 조회
    
    Args:
        include_test: 테스트 대화 포함 여부
    
    Returns:
        대화 목록 (날짜, 시간, 파일명 등)
    """
    ensure_storage_dir()
    if include_test:
        ensure_storage_dir(is_test=True)
    
    conversations = []
    
    # 일반 대화 읽기
    for filepath in sorted(STORAGE_DIR.glob("*.json"), reverse=True):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # end_report나 analysis가 None일 수도 있으므로 안전하게 처리
            end_report = data.get("end_report") or {}
            analysis = data.get("analysis") or {}
            
            conversations.append({
                "filename": filepath.name,
                "date": data.get("date", ""),
                "time": data.get("time", ""),
                "timestamp": data.get("timestamp", ""),
                "summary": end_report.get("summary", "대화 요약 없음"),
                "risk_score": analysis.get("risk_score", 0),
                "distress_level": analysis.get("emotional_distress", "낮음"),
                "is_test": False,
            })
        except Exception as e:
            # Windows 콘솔(cp949)에서 이모지 사용 시 UnicodeEncodeError가 발생할 수 있어 ASCII만 사용
            print(f"[WARN] 대화 파일 읽기 실패 ({filepath}): {e}")
    
    # 테스트 대화 읽기 (include_test가 True일 때만)
    if include_test:
        for filepath in sorted(TEST_STORAGE_DIR.glob("*.json"), reverse=True):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                end_report = data.get("end_report") or {}
                analysis = data.get("analysis") or {}
                
                conversations.append({
                    "filename": filepath.name,
                    "date": data.get("date", ""),
                    "time": data.get("time", ""),
                    "timestamp": data.get("timestamp", ""),
                    "summary": end_report.get("summary", "대화 요약 없음"),
                    "risk_score": analysis.get("risk_score", 0),
                    "distress_level": analysis.get("emotional_distress", "낮음"),
                    "is_test": True,
                })
            except Exception as e:
                print(f"[WARN] 테스트 대화 파일 읽기 실패 ({filepath}): {e}")
    
    return conversations


def get_conversation(filename: str, is_test: bool = False) -> Optional[Dict]:
    """
    특정 대화 상세 조회
    
    Args:
        filename: 파일명
        is_test: 테스트 대화 여부
    
    Returns:
        대화 데이터 또는 None
    """
    # 테스트 파일인지 확인 (test_ 접두사 또는 명시적 is_test)
    if filename.startswith("test_") or is_test:
        filepath = TEST_STORAGE_DIR / filename
    else:
        filepath = STORAGE_DIR / filename
    
    if not filepath.exists():
        return None
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 대화 파일 읽기 실패 ({filepath}): {e}")
        return None
