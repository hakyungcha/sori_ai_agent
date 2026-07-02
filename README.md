<div align="center">
  <img src="frontend/public/sori.png" alt="SORI 캐릭터" width="120" />
  <h1>SORI — 정서 지원 AI 에이전트</h1>
  <p>대화를 통해 학생의 정서 상태와 위기 신호를 추적하고,<br/>필요한 순간 도움으로 연결하는 FastAPI + React 기반 에이전트</p>

  <p>
    <img src="https://img.shields.io/badge/backend-FastAPI-009688" alt="FastAPI" />
    <img src="https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB" alt="React + Vite" />
    <img src="https://img.shields.io/badge/LLM-GPT--4o--mini-412991" alt="OpenAI GPT-4o-mini" />
    <img src="https://img.shields.io/badge/RAG-ChromaDB-FF6F00" alt="ChromaDB" />
  </p>
</div>

---

## 소개

SORI는 마음이 힘든 학생이 "한 단어부터" 편하게 이야기를 시작할 수 있도록 설계된 정서 지원 대화형 에이전트입니다. 대화가 이어지는 동안 정서적 고통 수준과 자살 위기 신호를 규칙 기반으로 계속 평가하고, 위험도가 높아지면 상담 연락처(1388, 112/119) 안내와 신뢰할 수 있는 어른에게 연결하는 흐름으로 대화를 이끕니다. 대화가 끝나면 관리자가 확인할 수 있는 종합 리포트를 생성합니다.

학생 자살 위기 대응 매뉴얼(`docs/학생자살위기대응_매뉴얼.txt`)을 벡터 DB(ChromaDB)에 저장해두고, 대화 중 관련 내용을 검색해 LLM 응답에 반영하는 RAG 구조를 사용합니다.

## 기획 배경 (제안 발표 자료)

과제 제안 시 작성한 기획서 14장입니다. 문제 정의 → 페르소나 → 에이전트 아키텍처 → 한계/개선 방향까지의 설계 흐름을 담고 있습니다.

> ⚠️ 6번(Agent Architecture) 슬라이드의 PostgreSQL은 초기 설계안 기준이며, 실제 구현체는 대화를 **JSON 파일**로 저장합니다. 자세한 내용은 아래 [아키텍처](#아키텍처) 섹션 참고.

<details>
<summary>기획서 펼쳐보기 (14장)</summary>

<table>
  <tr>
    <td align="center">1. 표지</td>
    <td align="center">2. Problem</td>
  </tr>
  <tr>
    <td><img src="docs/images/1.png" width="420" /></td>
    <td><img src="docs/images/2.png" width="420" /></td>
  </tr>
  <tr>
    <td align="center">3. Evidence</td>
    <td align="center">4. Approach</td>
  </tr>
  <tr>
    <td><img src="docs/images/3.png" width="420" /></td>
    <td><img src="docs/images/4.png" width="420" /></td>
  </tr>
  <tr>
    <td align="center">5. Persona</td>
    <td align="center">6. Agent Architecture</td>
  </tr>
  <tr>
    <td><img src="docs/images/5.png" width="420" /></td>
    <td><img src="docs/images/6.png" width="420" /></td>
  </tr>
  <tr>
    <td align="center">7. RAG Integration</td>
    <td align="center">8. Prompt Engineering</td>
  </tr>
  <tr>
    <td><img src="docs/images/7.png" width="420" /></td>
    <td><img src="docs/images/8.png" width="420" /></td>
  </tr>
  <tr>
    <td align="center">9. Status Tracking</td>
    <td align="center">10. Conversation</td>
  </tr>
  <tr>
    <td><img src="docs/images/9.png" width="420" /></td>
    <td><img src="docs/images/10.png" width="420" /></td>
  </tr>
  <tr>
    <td align="center">11. Admin Dashboard</td>
    <td align="center">12. Safety & Closure</td>
  </tr>
  <tr>
    <td><img src="docs/images/11.png" width="420" /></td>
    <td><img src="docs/images/12.png" width="420" /></td>
  </tr>
  <tr>
    <td align="center">13. Summary</td>
    <td align="center">14. Limitations & Future Improvement</td>
  </tr>
  <tr>
    <td><img src="docs/images/13.png" width="420" /></td>
    <td><img src="docs/images/14.png" width="420" /></td>
  </tr>
</table>

</details>

## 스크린샷

<table>
  <tr>
    <td align="center"><b>랜딩 화면</b></td>
    <td align="center"><b>대화 화면 (학생용)</b></td>
  </tr>
  <tr>
    <td><img src="docs/images/01_landing.png" width="420" /></td>
    <td><img src="docs/images/02_chat_user.png" width="420" /></td>
  </tr>
  <tr>
    <td align="center"><b>관리자 대시보드</b></td>
    <td align="center"><b>대화 상세 분석</b></td>
  </tr>
  <tr>
    <td><img src="docs/images/04_admin_dashboard.png" width="420" /></td>
    <td><img src="docs/images/05_admin_detail.png" width="420" /></td>
  </tr>
  <tr>
    <td align="center"><b>관리자 대화창 (JSON 출력 포함)</b></td>
    <td align="center"><b>대화 종료 시 종합 리포트</b></td>
  </tr>
  <tr>
    <td><img src="docs/images/03_chat_admin.png" width="420" /></td>
    <td><img src="docs/images/09_closing_message.png" width="420" /></td>
  </tr>
</table>

> 📁 원본 이미지: [`docs/images/`](docs/images/) — 평가용 JSON 출력 예시는 [`07_json_output.png`](docs/images/07_json_output.png), [`08_analysis_result.png`](docs/images/08_analysis_result.png)에서 확인할 수 있습니다.

## 주요 기능

- **친구 같은 대화 톤**: 상담사 어투가 아닌, 학생의 말을 반영(미러링)하며 공감하는 또래 친구 페르소나
- **정서/위기 신호 추적**: 매 턴마다 정서적 고통 수준(`낮음/중간/높음`), 자살 신호(`없음~높음`), 위험 점수(0~100)를 계산
- **단계별 개입**: 위험 점수에 따라 `일반대화 → 주의환기 → 전담자연계 → 즉시대응`으로 대응 수위를 조정
- **RAG 기반 응답**: 학생 자살 위기 대응 매뉴얼에서 관련 내용을 검색해 대화에 자연스럽게 반영
- **관리자 대시보드**: 저장된 모든 대화 목록과 상세 분석, 종합 리포트를 조회
- **평가용 JSON 뷰**: 관리자 모드에서 각 턴의 분석 결과를 JSON 형태로 그대로 확인 가능

## 기술 스택

| 영역 | 기술 |
| --- | --- |
| Backend | FastAPI, Pydantic, Uvicorn |
| Frontend | React 18, Vite |
| LLM | OpenAI `gpt-4o-mini` (Chat Completions API) |
| RAG | ChromaDB (로컬 벡터 DB) |
| 대화 저장 | JSON 파일 기반 (`backend/data/conversations/`) |

## 아키텍처

```
User ⇄ Frontend(React) ⇄ Backend(FastAPI)
                              │
                              ├─ 규칙 기반 정서/위기 분석 (agent.py)
                              │     └─ 정서 고통 수준 · 자살 신호 · 위험 점수 산출
                              │
                              ├─ RAG 검색 (rag.py + ChromaDB)
                              │     └─ 위기 대응 매뉴얼에서 관련 청크 검색
                              │
                              ├─ LLM 응답 생성 (llm.py, GPT-4o-mini)
                              │     └─ 페르소나 + RAG 컨텍스트 기반 응답
                              │
                              └─ 대화 저장 (storage.py)
                                    └─ JSON 파일로 대화/분석/리포트 기록
```

OPENAI_API_KEY가 없으면 LLM 호출 없이 규칙 기반 응답으로 자동 폴백합니다.

## 실행 방법

### 1) Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

`backend/.env` 파일을 만들고 아래 내용을 채워주세요.

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

```bash
uvicorn app.main:app --reload --port 8000
```

**RAG DB 초기화 (선택)** — 위기 대응 매뉴얼을 벡터 DB로 만들려면:

```bash
python init_rag_db.py
```

- 저장 위치: `backend/data/chroma_db/` (Git에는 포함되지 않음, `.gitignore` 처리됨)

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:5173` 접속. (`vite.config.js`의 `proxy` 설정으로 `/api` 요청이 백엔드로 전달됩니다. 8000번 포트가 다른 프로세스에 이미 점유돼 있다면 백엔드/`vite.config.js` 포트를 함께 바꿔주세요.)

## API

| Method | Endpoint | 설명 |
| --- | --- | --- |
| POST | `/api/chat` | 대화 메시지 전송, 정서/위기 분석 및 응답 반환 |
| GET | `/api/rag/info` | RAG DB 정보 (저장 위치, 청크 개수 등) |
| GET | `/api/admin/conversations` | 저장된 대화 목록 조회 |
| GET | `/api/admin/conversations/{filename}` | 특정 대화 상세 조회 |
| GET | `/health` | 헬스 체크 |

`POST /api/chat` 요청/응답 예시:

```json
// Request
{ "history": [{ "role": "user", "content": "..." }], "message": "...", "is_admin": false }

// Response
{
  "reply": "많이 힘들었겠구나. 어떤 상황이었는지 조금 더 말해줄래?",
  "emotional_distress": "높음",
  "suicide_signal": "낮음",
  "risk_score": 45,
  "next_action": "주의환기",
  "conversation_end": false,
  "end_report": null
}
```

## 관리자 모드 (평가용)

1. 랜딩 페이지에서 "관리자 로그인" 클릭
2. 아이디 `admin` / 비밀번호 `1234` (데모용 임시 계정)로 로그인
3. 채팅 화면의 "상태 대시보드" 패널에서 실시간 분석 결과 확인
4. "JSON 보기" 버튼으로 각 턴의 원본 분석 JSON 확인

학생 화면은 AI 답변만 노출하고, 관리자 화면은 정서/위기 분석 정보와 JSON 출력까지 모두 노출합니다.

## Windows에서 자주 발생하는 오류

<details>
<summary>펼쳐서 보기</summary>

**PowerShell에서 가상환경/npm 스크립트 실행이 막힐 때**

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1   # 또는 npm run dev
```

**`uvicorn` 명령어를 인식하지 못할 때**

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**포트 충돌 (`[WinError 10048]`)**

```powershell
netstat -ano | findstr :8000
taskkill /F /PID <PID>
```

**백엔드 500 에러 + `UnicodeEncodeError: 'cp949'`**

Windows 콘솔 기본 인코딩(cp949) 때문에 이모지 출력이 실패할 수 있습니다. 로그에는 이모지 대신 `[WARN]`, `[ERR]` 같은 ASCII 문자열만 사용하세요.

</details>

## 참고 자료

- [학생자살위기대응_매뉴얼.txt](docs/학생자살위기대응_매뉴얼.txt) — RAG의 근거 데이터로 사용되는 위기 대응 매뉴얼
</content>
