# 정서 지원 에이전트 (FastAPI + React)

대화 기반으로 정서 상태와 위기 신호를 추적하고, 종료 시 종합 리포트를 출력하는 시안입니다.

## 실행 방법

### 1) Backend
```bash
cd backend
copy env.example .env
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

`.env`에 `OPENAI_API_KEY`와 `OPENAI_MODEL`을 설정하면 LLM 응답을 사용합니다.

### RAG DB 초기화 (선택사항)

매뉴얼 기반 RAG를 사용하려면 벡터 DB를 초기화해야 합니다:

```bash
cd backend
python init_rag_db.py
```

**저장 위치**: `backend/data/chroma_db/`
- 이 폴더에 ChromaDB 파일이 저장됩니다
- 직접 확인 가능하며, Git에 포함되지 않습니다 (`.gitignore`에 추가 권장)

### 2) Frontend
```bash
cd frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:5173`로 접속하세요.

## API
- `POST /api/chat`
  - 요청: `{ "history": [{ "role": "user|ai", "content": "..." }], "message": "..." }`
  - 응답: 정서 상태/자살 신호/리스크 점수/종합 리포트 포함
- `GET /api/rag/info`
  - RAG DB 정보 확인 (저장 위치, 청크 개수 등)

## RAG (Retrieval-Augmented Generation)

이 프로젝트는 학생 자살 위기 대응 매뉴얼을 벡터 DB에 저장하고, 대화 중 관련 내용을 검색하여 LLM 응답에 반영합니다.

- **매뉴얼 위치**: `docs/학생자살위기대응_매뉴얼.txt`
- **벡터 DB 위치**: `backend/data/chroma_db/`
- **초기화**: `python backend/init_rag_db.py` 실행

## 관리자 모드 (과제 평가용)

**JSON 출력 확인 방법:**
1. 랜딩 페이지에서 "관리자 로그인" 클릭
2. 아이디와 비밀번호 입력 (임시: 아이디: admin, 비밀번호: 1234)
3. 로그인 후 채팅 화면에서 "상태 대시보드 (관리자용)" 패널 확인
4. "JSON 보기" 버튼 클릭하여 JSON 형식 출력 확인

**JSON 출력 예시:**
```json
{
  "답변": "많이 힘들었겠구나. 어떤 상황이었는지 조금 더 말해줄래?",
  "정서적 고통 상태": "높음",
  "자살 신호": "낮음",
  "위험 점수": 45,
  "다음 조치": "주의환기",
  "대화 종료": false,
  "종합 결과": null
}
```

**학생 화면 vs 관리자 화면:**
- **학생 화면**: AI 답변만 표시 (상태 정보 숨김)
- **관리자 화면**: 모든 상태 정보 + JSON 출력 가능
