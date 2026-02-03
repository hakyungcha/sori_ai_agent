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

## 자주 발생하는 오류와 해결 방법 (Windows)

### 1) PowerShell에서 `.venv\Scripts\Activate.ps1` 실행이 막힐 때

에러 메시지 예시:

```text
.venv\Scripts\Activate.ps1 : 이 시스템에서 스크립트를 실행할 수 없으므로 ...
PSSecurityException
```

**해결 방법 (현재 PowerShell 창에서만 임시 허용):**

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

첫 줄은 **현재 창에서만** 스크립트 실행을 허용하고, 둘째 줄에서 가상환경을 활성화합니다.

### 2) `uvicorn` 명령어를 인식하지 못할 때

에러 메시지 예시:

```text
uvicorn : 'uvicorn' 용어가 cmdlet, 함수, 스크립트 파일 또는 실행할 수 있는 프로그램 이름으로 인식되지 않습니다.
```

**해결 방법:**

- 가상환경이 활성화된 상태에서 다음과 같이 실행합니다:

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3) 포트 충돌 (`[WinError 10048]` 등)로 서버가 안 켜질 때

에러 메시지 예시:

```text
[Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000)
각 소켓 주소(프로토콜/네트워크 주소/포트)는 하나만 사용할 수 있습니다
```

**해결 방법: 8000 포트를 사용하는 프로세스 종료**

```powershell
netstat -ano | findstr :8000
taskkill /F /PID <PID>
```

여기서 `<PID>`는 `netstat` 결과에서 8000 포트를 점유하고 있는 프로세스 ID입니다.  
여러 개가 복잡하면 아래처럼 파이썬 프로세스를 한 번에 종료할 수도 있습니다:

```powershell
taskkill /F /IM python.exe
```

### 4) 백엔드 500 에러 + 콘솔에서 `UnicodeEncodeError: 'cp949'`가 뜰 때

Windows 콘솔의 기본 인코딩(cp949)에서 이모지나 일부 문자를 출력할 수 없어서 발생합니다.

**해결 방법(이미 적용된 코드 기준):**

- `print()`에 이모지(예: 😢, ⚠️ 등)를 사용하지 않고, `[WARN]`, `[ERR]` 같은 ASCII 문자열로만 로깅합니다.
- 만약 직접 로그를 추가할 때도 **이모지 대신 영문/숫자만 사용**합니다.

### 5) `npm run dev` 실행 시 PowerShell에서 `npm.ps1` 보안 오류가 날 때

에러 메시지 예시:

```text
npm : 이 시스템에서 스크립트를 실행할 수 없으므로 C:\Program Files\nodejs\npm.ps1 파일을 로드할 수 없습니다.
PSSecurityException
```

**해결 방법 (현재 PowerShell 창에서만 임시 허용):**

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
npm run dev
```

또는 PowerShell 대신 **명령 프롬프트(cmd)**를 열고 아래처럼 실행할 수도 있습니다:

```cmd
cd C:\GenesisLAB\frontend
npm run dev
```

### 6) 브라우저에서 “페이지를 표시할 수 없음”일 때 체크 리스트

- **백엔드**:
  - PowerShell 창에 아래와 같은 로그가 떠 있는지 확인:

    ```text
    Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
    ```

  - 브라우저에서 `http://localhost:8000/docs` 접속 → FastAPI 문서 페이지가 보이면 정상.

- **프론트엔드**:
  - `frontend` 폴더에서:

    ```powershell
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    npm run dev
    ```

  - 브라우저에서 `http://localhost:5173` 접속.

백엔드/프론트 둘 다 켜져 있어야 전체 서비스(SORI)가 정상적으로 동작합니다.
