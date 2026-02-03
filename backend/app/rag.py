"""
RAG (Retrieval-Augmented Generation) 모듈
학생 자살 위기 대응 매뉴얼을 벡터 DB에 저장하고 검색하는 기능
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

import chromadb
from chromadb.config import Settings

# ChromaDB 저장 위치: backend/data/chroma_db
# 사용자가 직접 확인할 수 있는 위치
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "chroma_db"
MANUAL_PATH = BASE_DIR.parent / "docs" / "학생자살위기대응_매뉴얼.txt"

COLLECTION_NAME = "suicide_prevention_manual"


def _get_client() -> chromadb.Client:
    """ChromaDB 클라이언트 생성"""
    DB_PATH.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(DB_PATH),
        settings=Settings(anonymized_telemetry=False)
    )


def _chunk_manual() -> List[dict]:
    """
    매뉴얼 파일을 청킹하여 반환
    섹션 단위로 나누고, 각 청크에 메타데이터 추가
    """
    if not MANUAL_PATH.exists():
        return []
    
    chunks = []
    current_section = ""
    current_content = []
    chunk_id = 0
    
    with open(MANUAL_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # 섹션 헤더 감지
        if "1단계" in line or "2단계" in line or "3단계" in line:
            # 이전 청크 저장
            if current_content:
                chunks.append({
                    "id": str(chunk_id),
                    "text": "\n".join(current_content),
                    "section": current_section,
                    "metadata": {"section": current_section, "chunk_id": chunk_id}
                })
                chunk_id += 1
                current_content = []
            current_section = line
            current_content.append(line)
        elif "자살" in line and ("징후" in line or "위험" in line or "개입" in line):
            # 섹션 제목 감지
            if current_content:
                chunks.append({
                    "id": str(chunk_id),
                    "text": "\n".join(current_content),
                    "section": current_section,
                    "metadata": {"section": current_section, "chunk_id": chunk_id}
                })
                chunk_id += 1
                current_content = []
            current_section = line
            current_content.append(line)
        elif line and not line.startswith("===") and not line.startswith("Page"):
            # 내용 추가
            current_content.append(line)
    
    # 마지막 청크 저장
    if current_content:
        chunks.append({
            "id": str(chunk_id),
            "text": "\n".join(current_content),
            "section": current_section or "기타",
            "metadata": {"section": current_section or "기타", "chunk_id": chunk_id}
        })
    
    # 너무 짧은 청크는 병합
    merged_chunks = []
    temp_chunk = None
    
    for chunk in chunks:
        if len(chunk["text"]) < 100 and temp_chunk:
            # 이전 청크와 병합
            temp_chunk["text"] += "\n\n" + chunk["text"]
            temp_chunk["metadata"]["section"] = chunk["section"]
        else:
            if temp_chunk:
                merged_chunks.append(temp_chunk)
            temp_chunk = chunk
    
    if temp_chunk:
        merged_chunks.append(temp_chunk)
    
    return merged_chunks


def init_db() -> bool:
    """
    매뉴얼을 벡터 DB에 저장
    저장 위치: backend/data/chroma_db
    """
    try:
        client = _get_client()
        
        # 기존 컬렉션이 있으면 삭제하고 재생성
        try:
            client.delete_collection(COLLECTION_NAME)
        except:
            pass
        
        collection = client.create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "학생 자살 위기 대응 매뉴얼"}
        )
        
        chunks = _chunk_manual()
        if not chunks:
            print(f"⚠️ 매뉴얼 파일을 찾을 수 없습니다: {MANUAL_PATH}")
            return False
        
        # 청크를 DB에 추가
        texts = [chunk["text"] for chunk in chunks]
        ids = [chunk["id"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        collection.add(
            documents=texts,
            ids=ids,
            metadatas=metadatas
        )
        
        print(f"✅ {len(chunks)}개의 청크를 ChromaDB에 저장했습니다.")
        print(f"📁 저장 위치: {DB_PATH.absolute()}")
        return True
    
    except Exception as e:
        print(f"❌ DB 초기화 실패: {e}")
        return False


def search_relevant_chunks(
    query: str,
    history: List,
    n_results: int = 3
) -> List[str]:
    """
    대화 내용을 기반으로 관련 매뉴얼 청크 검색
    
    Args:
        query: 현재 사용자 메시지
        history: 대화 히스토리
        n_results: 반환할 청크 개수
    
    Returns:
        관련 청크 텍스트 리스트
    """
    try:
        client = _get_client()
        
        # 컬렉션이 존재하는지 확인
        try:
            collection = client.get_collection(COLLECTION_NAME)
        except Exception:
            # DB가 초기화되지 않았으면 빈 리스트 반환
            return []
        
        # 최근 대화 내용을 쿼리에 추가하여 컨텍스트 확보
        recent_context = query
        if history:
            recent_messages = [turn.content for turn in history[-3:] if turn.role == "user"]
            if recent_messages:
                recent_context = " ".join(recent_messages) + " " + query
        
        # 벡터 검색
        results = collection.query(
            query_texts=[recent_context],
            n_results=n_results
        )
        
        if results and results["documents"] and len(results["documents"][0]) > 0:
            return results["documents"][0]
        
        return []
    
    except Exception as e:
        # 모든 예외를 잡아서 빈 리스트 반환 (대화가 중단되지 않도록)
        print(f"⚠️ RAG 검색 실패 (계속 진행): {e}")
        return []


def get_db_info() -> dict:
    """DB 정보 반환 (확인용)"""
    try:
        client = _get_client()
        collection = client.get_collection(COLLECTION_NAME)
        count = collection.count()
        return {
            "path": str(DB_PATH.absolute()),
            "collection": COLLECTION_NAME,
            "chunk_count": count,
            "exists": True
        }
    except:
        return {
            "path": str(DB_PATH.absolute()),
            "collection": COLLECTION_NAME,
            "chunk_count": 0,
            "exists": False
        }
