"""
RAG DB 초기화 스크립트
매뉴얼을 벡터 DB에 저장하는 스크립트

사용법:
    python init_rag_db.py
"""
from app.rag import init_db, get_db_info

if __name__ == "__main__":
    print("🚀 RAG DB 초기화 시작...")
    print("=" * 50)
    
    success = init_db()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ DB 초기화 완료!")
        info = get_db_info()
        print(f"\n📊 DB 정보:")
        print(f"  - 저장 위치: {info['path']}")
        print(f"  - 컬렉션: {info['collection']}")
        print(f"  - 청크 개수: {info['chunk_count']}")
        print(f"\n💡 이 위치에서 ChromaDB 파일을 직접 확인할 수 있습니다.")
    else:
        print("\n❌ DB 초기화 실패. 매뉴얼 파일 경로를 확인해주세요.")
