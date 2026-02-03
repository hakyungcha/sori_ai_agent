import { useEffect, useMemo, useRef, useState } from "react";
import { sendChat } from "./api.js";
import AdminPage from "./AdminPage.jsx";

const initialHistory = [
  {
    role: "ai",
    content:
      "안녕, 난 SORI야. 오늘 마음이 어땠는지 편하게 얘기해줘. " +
      "한 가지만 말해도 괜찮아.",
  },
];

export default function App() {
  const [history, setHistory] = useState(initialHistory);
  const [message, setMessage] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [started, setStarted] = useState(false);
  const [showAdminLogin, setShowAdminLogin] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false); // 관리자 모드 여부
  const [showAdminPage, setShowAdminPage] = useState(false); // 관리자 페이지 표시 여부
  const [showAdminDropdown, setShowAdminDropdown] = useState(false); // 관리자 드롭다운 메뉴 표시
  const [showJsonOutput, setShowJsonOutput] = useState(false); // JSON 출력 표시 여부
  const [loginError, setLoginError] = useState(""); // 로그인 에러 메시지
  const [showEndModal, setShowEndModal] = useState(false); // 대화 종료 모달
  const chatWindowRef = useRef(null);

  // 관리자 로그인 처리
  const handleAdminLogin = () => {
    // 랜딩 페이지의 로그인 폼 사용
    const id = document.getElementById("admin-id")?.value;
    const password = document.getElementById("admin-password")?.value;
    
    setLoginError("");
    
    if (!id || !password) {
      setLoginError("아이디와 비밀번호를 입력해주세요.");
      return;
    }
    
    // 관리자 인증 (아이디: admin, 비밀번호: 1234)
    if (id === "admin" && password === "1234") {
      setIsAdmin(true);
      setShowAdminLogin(false);
      setShowAdminPage(false); // 로그인만 하고 페이지는 이동하지 않음
      setLoginError("");
      // 입력 필드 초기화
      document.getElementById("admin-id").value = "";
      document.getElementById("admin-password").value = "";
    } else {
      setLoginError("아이디 또는 비밀번호가 올바르지 않습니다.");
    }
  };

  const canSend = useMemo(
    () => message.trim().length > 0 && !loading,
    [message, loading]
  );

  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [history]);

  // 브라우저 뒤로가기 처리
  useEffect(() => {
    const handlePopState = (event) => {
      if (started) {
        handleReset();
        setStarted(false);
      }
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, [started]);

  // 드롭다운 외부 클릭 시 닫기
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showAdminDropdown && !event.target.closest('.admin-dropdown-container')) {
        setShowAdminDropdown(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showAdminDropdown]);

  // 채팅 화면으로 이동할 때 히스토리 추가
  useEffect(() => {
    if (started) {
      window.history.pushState({ page: "chat" }, "", window.location.href);
    }
  }, [started]);

  const handleSend = async () => {
    if (!canSend) return;
    const nextHistory = [...history, { role: "user", content: message }];
    setHistory(nextHistory);
    setMessage("");
    setError("");
    setLoading(true);

    try {
      const response = await sendChat({
        history: nextHistory,
        message,
      }, isAdmin);
      setAnalysis(response);
      setHistory((prev) => [...prev, { role: "ai", content: response.reply }]);
      setError(""); // 성공 시 에러 메시지 초기화
      if (response.conversation_end) {
        setShowEndModal(true);
      }
    } catch (err) {
      console.error("채팅 전송 오류:", err);
      const errorMessage = err.message || "오류가 발생했습니다. 잠시 후 다시 시도해주세요.";
      setError(errorMessage);
      // 에러 발생 시에도 기본 응답 추가
      setHistory((prev) => [
        ...prev,
        { role: "ai", content: "죄송해요, 잠시 문제가 생겼어요. 다시 말해줄 수 있을까?" }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setHistory(initialHistory);
    setMessage("");
    setAnalysis(null);
    setError("");
  };

  const handleChipClick = async (chipText) => {
    setStarted(true);
    const userMessage = chipText;
    const nextHistory = [...history, { role: "user", content: userMessage }];
    setHistory(nextHistory);
    setError("");
    setLoading(true);

    try {
      const response = await sendChat({
        history: nextHistory,
        message: userMessage,
      }, isAdmin);
      setAnalysis(response);
      setHistory((prev) => [...prev, { role: "ai", content: response.reply }]);
      setError(""); // 성공 시 에러 메시지 초기화
      if (response.conversation_end) {
        setShowEndModal(true);
      }
    } catch (err) {
      console.error("칩 클릭 전송 오류:", err);
      const errorMessage = err.message || "오류가 발생했습니다. 잠시 후 다시 시도해주세요.";
      setError(errorMessage);
      // 에러 발생 시에도 기본 응답 추가
      setHistory((prev) => [
        ...prev,
        { role: "ai", content: "죄송해요, 잠시 문제가 생겼어요. 다시 말해줄 수 있을까?" }
      ]);
    } finally {
      setLoading(false);
    }
  };

  // 관리자 페이지 표시 (가장 먼저 체크)
  if (showAdminPage) {
    return (
      <AdminPage
        onBack={() => {
          setShowAdminPage(false);
        }}
        onLogout={() => {
          setIsAdmin(false);
          setShowAdminPage(false);
        }}
      />
    );
  }

  if (!started) {
    return (
      <div className="app">
        <header className="header landing-header">
          <div className="landing-topbar">
            <span className="brand">SORI</span>
            {/* 관리자 프로필 아이콘 또는 로그인 버튼 */}
            <div style={{ position: "relative" }} className="admin-dropdown-container">
              {isAdmin ? (
                <div style={{ position: "relative", display: "flex", flexDirection: "column", alignItems: "center", gap: "4px" }}>
                  <button
                    type="button"
                    onClick={() => setShowAdminDropdown(!showAdminDropdown)}
                    style={{
                      width: "40px",
                      height: "40px",
                      borderRadius: "50%",
                      background: "#1e3a5f",
                      border: "none",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: "white",
                      fontSize: "18px",
                      fontWeight: "bold",
                    }}
                  >
                    A
                  </button>
                  {showAdminDropdown && (
                    <div
                      style={{
                        position: "absolute",
                        top: "52px",
                        right: "0",
                        background: "white",
                        border: "1px solid #e5e5e5",
                        borderRadius: "8px",
                        boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                        minWidth: "180px",
                        zIndex: 1000,
                        padding: "8px 0",
                      }}
                    >
                      <button
                        type="button"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          setShowAdminPage(true);
                          setShowAdminDropdown(false);
                        }}
                        style={{
                          width: "100%",
                          padding: "14px 20px",
                          textAlign: "left",
                          background: "none",
                          border: "none",
                          cursor: "pointer",
                          fontSize: "15px",
                          color: "#1e3a5f",
                          fontWeight: "500",
                          display: "flex",
                          alignItems: "center",
                          gap: "10px",
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = "#f0f7ff";
                          e.currentTarget.style.color = "#1e3a5f";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = "white";
                          e.currentTarget.style.color = "#1e3a5f";
                        }}
                      >
                        <span style={{ fontSize: "18px" }}>📊</span>
                        <span>대시보드</span>
                      </button>
                      <div style={{ 
                        height: "1px", 
                        background: "#e5e5e5", 
                        margin: "4px 0" 
                      }} />
                      <button
                        type="button"
                        onClick={() => {
                          setIsAdmin(false);
                          setShowAdminDropdown(false);
                        }}
                        style={{
                          width: "100%",
                          padding: "14px 20px",
                          textAlign: "left",
                          background: "none",
                          border: "none",
                          cursor: "pointer",
                          fontSize: "15px",
                          color: "#dc2626",
                          fontWeight: "500",
                          display: "flex",
                          alignItems: "center",
                          gap: "10px",
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = "#fee2e2";
                          e.currentTarget.style.color = "#dc2626";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = "white";
                          e.currentTarget.style.color = "#dc2626";
                        }}
                      >
                        <span style={{ fontSize: "18px" }}>🚪</span>
                        <span>로그아웃</span>
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <button
                  type="button"
                  className="ghost admin-link"
                  onClick={() => setShowAdminLogin((prev) => !prev)}
                >
                  관리자 로그인
                </button>
              )}
            </div>
          </div>
        </header>
        <section className="hero-stage">
          <div className="hero-text">
            <p>
              <span className="hero-line main">안녕, 나는 SORI야.</span>
              <span className="hero-line">여기서는 괜찮지 않아도 돼.</span>
              <span className="hero-line">한 단어부터 시작해볼래?</span>
            </p>
          </div>
          <div className="sori-avatar" aria-hidden="true">
            <img src="/sori.png" alt="SORI 캐릭터" className="sori-image" />
          </div>
          <div className="talk-bubble hero-bubble">
            <span className="bubble-label">SORI</span>
            <p>요즘 마음이 어때? 한 단어여도 괜찮아.</p>
            <div className="chip-row">
              <button
                type="button"
                className="chip"
                onClick={() => handleChipClick("피곤해")}
              >
                피곤해
              </button>
              <button
                type="button"
                className="chip"
                onClick={() => handleChipClick("불안해")}
              >
                불안해
              </button>
              <button
                type="button"
                className="chip"
                onClick={() => handleChipClick("답답해")}
              >
                답답해
              </button>
              <button
                type="button"
                className="chip"
                onClick={() => handleChipClick("그냥 그래")}
              >
                그냥 그래
              </button>
            </div>
            <div className="bubble-divider" />
            <div className="bubble-trust">
              <span>응급 상황이면 112 / 119</span>
              <span>청소년 상담 1388</span>
              <span>필요하면 언제든 멈춰도 괜찮아</span>
            </div>
          </div>
          <span className="hero-cta-note">SORI와 바로 연결돼요</span>
          <button type="button" onClick={() => setStarted(true)}>
            지금, 조금 털어놓기
          </button>
        </section>
        {showAdminLogin ? (
          <div className="modal-overlay" onClick={() => setShowAdminLogin(false)}>
            <div
              className="admin-modal"
              onClick={(event) => event.stopPropagation()}
            >
              <div className="admin-modal-header">
                <h3>관리자 로그인</h3>
                <button
                  type="button"
                  className="ghost"
                  onClick={() => setShowAdminLogin(false)}
                >
                  닫기
                </button>
              </div>
              <p>관리자 전용 대시보드와 설정 화면은 로그인 후 접근할 수 있어요.</p>
              {loginError && (
                <div style={{ 
                  padding: "8px 12px", 
                  background: "#fee2e2", 
                  color: "#dc2626", 
                  borderRadius: "6px",
                  marginBottom: "12px",
                  fontSize: "14px"
                }}>
                  {loginError}
                </div>
              )}
              <div className="admin-form">
                <input 
                  type="text" 
                  placeholder="아이디" 
                  id="admin-id"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      document.getElementById("admin-password")?.focus();
                    }
                  }}
                />
                <input 
                  type="password" 
                  placeholder="비밀번호" 
                  id="admin-password"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      handleAdminLogin();
                    }
                  }}
                />
                <button 
                  type="button"
                  onClick={handleAdminLogin}
                >
                  로그인
                </button>
              </div>
              <div className="admin-links">
                <button type="button" className="ghost">
                  회원가입
                </button>
                <button type="button" className="ghost">
                  비밀번호 찾기
                </button>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <button
              type="button"
              className="chat-brand"
              onClick={() => {
                handleReset();
                setStarted(false);
              }}
              aria-label="SORI 홈으로 이동"
            >
              <img src="/sori.png" alt="SORI 캐릭터" className="chat-brand-logo" />
              <span className="chat-brand-title">SORI</span>
            </button>
          </div>
          
          {/* 관리자 프로필 아이콘 (로그인된 경우에만 표시) */}
          {isAdmin && (
            <div style={{ position: "relative" }} className="admin-dropdown-container">
              <div style={{ position: "relative", display: "flex", flexDirection: "column", alignItems: "center", gap: "4px" }}>
                <button
                  type="button"
                  onClick={() => setShowAdminDropdown(!showAdminDropdown)}
                  style={{
                    width: "40px",
                    height: "40px",
                    borderRadius: "50%",
                    background: "#1e3a5f",
                    border: "none",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "white",
                    fontSize: "18px",
                    fontWeight: "bold",
                  }}
                >
                  A
                </button>
                {showAdminDropdown && (
                  <div
                    style={{
                      position: "absolute",
                      top: "52px",
                      right: "0",
                      background: "white",
                      border: "1px solid #e5e5e5",
                      borderRadius: "8px",
                      boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                      minWidth: "180px",
                      zIndex: 1000,
                      padding: "8px 0",
                    }}
                  >
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setShowAdminPage(true);
                        setShowAdminDropdown(false);
                      }}
                      style={{
                        width: "100%",
                        padding: "14px 20px",
                        textAlign: "left",
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        fontSize: "15px",
                        color: "#1e3a5f",
                        fontWeight: "500",
                        display: "flex",
                        alignItems: "center",
                        gap: "10px",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = "#f0f7ff";
                        e.currentTarget.style.color = "#1e3a5f";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = "white";
                        e.currentTarget.style.color = "#1e3a5f";
                      }}
                    >
                      <span style={{ fontSize: "18px" }}>📊</span>
                      <span>대시보드</span>
                    </button>
                    <div style={{ 
                      height: "1px", 
                      background: "#e5e5e5", 
                      margin: "4px 0" 
                    }} />
                    <button
                      type="button"
                      onClick={() => {
                        setIsAdmin(false);
                        setShowAdminDropdown(false);
                      }}
                      style={{
                        width: "100%",
                        padding: "14px 20px",
                        textAlign: "left",
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        fontSize: "15px",
                        color: "#dc2626",
                        fontWeight: "500",
                        display: "flex",
                        alignItems: "center",
                        gap: "10px",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = "#fee2e2";
                        e.currentTarget.style.color = "#dc2626";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = "white";
                        e.currentTarget.style.color = "#dc2626";
                      }}
                    >
                      <span style={{ fontSize: "18px" }}>🚪</span>
                      <span>로그아웃</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </header>
      <section className="hero">
        <div>
          <h2>오늘의 마음 상태를 안전하게 기록해요</h2>
          <p>
            감정 신호를 놓치지 않고, 필요한 순간에 도움으로 이어질 수 있도록
            설계된 학생 친화형 인터페이스입니다.
          </p>
        </div>
        <div className="hero-badges">
          <span>차분한 대화 톤</span>
          <span>과정 중심 기록</span>
          <span>안전 신호 추적</span>
        </div>
      </section>

      <main className="grid">
        <section className="panel">
          <div className="panel-header">
            <h2>대화</h2>
            <div className="panel-actions">
            <button type="button" onClick={handleReset} className="ghost">
              초기화
            </button>
            </div>
          </div>
          <div className="chat-window" ref={chatWindowRef}>
            {history.map((turn, index) => (
              <div
                key={`${turn.role}-${index}`}
                className={`message-wrapper ${turn.role}`}
              >
                <div className={`bubble ${turn.role}`}>
                  <p>{turn.content}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="composer">
            <textarea
              rows={3}
              placeholder="대화를 입력하세요"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  handleSend();
                }
              }}
              disabled={analysis?.conversation_end || showEndModal}
            />
            <button
              type="button"
              onClick={handleSend}
              disabled={!canSend || analysis?.conversation_end || showEndModal}
            >
              {loading ? "전송 중..." : "전송"}
            </button>
          </div>
          {error ? (
            <div className="error" style={{ 
              padding: "12px", 
              background: "#fee2e2", 
              borderRadius: "8px",
              marginTop: "8px"
            }}>
              <strong>⚠️ 오류:</strong> {error}
              <br />
              <small style={{ fontSize: "12px", color: "#666" }}>
                백엔드 서버가 실행 중인지 확인해주세요. (http://localhost:8000)
              </small>
            </div>
          ) : null}
        </section>

        {/* 관리자 모드에서만 상태 대시보드 표시 */}
        {isAdmin && (
          <section className="panel">
            <div className="panel-header">
              <h2>📊 상태 대시보드 (관리자용)</h2>
              <div className="panel-actions">
                <button
                  type="button"
                  onClick={() => setShowJsonOutput(!showJsonOutput)}
                  className="ghost"
                  style={{ 
                    background: showJsonOutput ? "#1e3a5f" : "transparent",
                    color: showJsonOutput ? "white" : "inherit"
                  }}
                >
                  {showJsonOutput ? "📋 표 형식" : "📄 JSON 보기"}
                </button>
              </div>
            </div>
            {analysis ? (
              showJsonOutput ? (
                // JSON 형식 출력 (과제 평가용)
                <div className="json-output">
                  <pre>{JSON.stringify({
                    "답변": analysis.reply,
                    "정서적 고통 상태": analysis.emotional_distress,
                    "자살 신호": analysis.suicide_signal,
                    "위험 점수": analysis.risk_score,
                    "다음 조치": analysis.next_action,
                    "대화 종료": analysis.conversation_end,
                    "종합 결과": analysis.end_report ? {
                      "대화 요약": analysis.end_report.summary,
                      "최종 위험 점수": analysis.end_report.risk_score,
                      "상태 추이": analysis.end_report.trend,
                      "다음 대화 시 가이드": analysis.end_report.next_guidance,
                      "최종 정서적 고통 수준": analysis.end_report.distress_level,
                      "최종 자살 신호": analysis.end_report.suicide_signal,
                      "대화 턴 수": analysis.end_report.conversation_turns,
                      "주요 주제": analysis.end_report.key_topics
                    } : null
                  }, null, 2)}</pre>
                </div>
              ) : (
                // 표 형식 출력
                <div className="status">
                  <div>
                    <span>정서적 고통</span>
                    <strong>{analysis.emotional_distress}</strong>
                  </div>
                  <div>
                    <span>자살 신호</span>
                    <strong>{analysis.suicide_signal}</strong>
                  </div>
                  <div>
                    <span>위험 점수</span>
                    <strong>{analysis.risk_score}</strong>
                  </div>
                  <div>
                    <span>다음 조치</span>
                    <strong>{analysis.next_action}</strong>
                  </div>
                  <div>
                    <span>대화 종료</span>
                    <strong>{analysis.conversation_end ? "예" : "아니오"}</strong>
                  </div>
                </div>
              )
            ) : (
              <p className="empty">대화를 전송하면 상태가 표시됩니다.</p>
            )}
          </section>
        )}

        {!isAdmin && (
          <aside className="side-stack">
            {analysis?.conversation_end ? (
              <section className="panel side-panel">
                <div className="panel-header">
                  <h2>대화가 마무리됐어</h2>
                </div>
                <p className="side-text">
                  여기까지 이야기해줘서 고마워. 필요하면 언제든 다시 시작할 수 있어.
                </p>
                <button
                  type="button"
                  className="primary side-button"
                  onClick={() => {
                    handleReset();
                    setStarted(false);
                  }}
                >
                  처음 화면으로 돌아가기
                </button>
              </section>
            ) : (
              <>
                <section className="panel side-panel">
                  <div className="panel-header">
                    <h2>지금 할 수 있는 것</h2>
                  </div>
                  <ul className="side-list">
                    <li>그냥 아무 말이나 적어보기</li>
                    <li>오늘 있었던 일 하나만 말하기</li>
                    <li>잠깐 쉬었다가 돌아오기</li>
                    <li>SORI가 먼저 질문하게 하기</li>
                  </ul>
                  <div className="side-chip-row">
                    <button type="button" className="chip ghost-chip" onClick={() => handleChipClick("그냥 그래")}>
                      그냥 그래
                    </button>
                    <button type="button" className="chip ghost-chip" onClick={() => handleChipClick("말하기 어려워")}>
                      말하기 어려워
                    </button>
                  </div>
                </section>
                <section className="panel side-panel">
                  <div className="panel-header">
                    <h2>SORI의 태도</h2>
                  </div>
                  <p className="side-text">
                    여기서는 정답도, 평가도 없어요. 서두르지 않고, 말하고 싶을 때까지 기다릴게요.
                  </p>
                  <div className="side-note">
                    하고 싶은 만큼만 말해도 괜찮아.
                  </div>
                </section>
              </>
            )}
          </aside>
        )}


        {/* 관리자 모드: 대화 중에도 JSON 출력 표시 */}
        {isAdmin && analysis && !analysis.conversation_end && (
          <section className="panel">
            <div className="panel-header">
              <h2>📄 JSON 출력 (관리자용)</h2>
            </div>
            <div className="json-output">
              <pre>{JSON.stringify({
                "답변": analysis.reply,
                "정서적 고통 상태": analysis.emotional_distress,
                "자살 신호": analysis.suicide_signal,
                "위험 점수": analysis.risk_score,
                "다음 조치": analysis.next_action,
                "대화 종료": analysis.conversation_end,
              }, null, 2)}</pre>
            </div>
          </section>
        )}

        {/* 대화 종료 시: 학생에게는 친근한 메시지, 관리자에게는 전체 리포트 */}
        {analysis?.conversation_end && (
          <section className="panel">
            <h2>{isAdmin ? "종합 리포트" : "대화를 마무리하며"}</h2>
            {analysis.end_report ? (
              <div className="report">
                {isAdmin ? (
                  // 관리자: 전체 리포트 표시
                  <>
                    <p><strong>대화 요약:</strong> {analysis.end_report.summary}</p>
                    <div className="report-meta">
                      <span>위험 점수</span>
                      <strong>{analysis.end_report.risk_score}</strong>
                    </div>
                    <div className="report-meta">
                      <span>상태 추이</span>
                      <strong>{analysis.end_report.trend}</strong>
                    </div>
                    <div className="report-meta">
                      <span>정서적 고통</span>
                      <strong>{analysis.end_report.distress_level}</strong>
                    </div>
                    <div className="report-meta">
                      <span>자살 신호</span>
                      <strong>{analysis.end_report.suicide_signal}</strong>
                    </div>
                    <div className="report-meta">
                      <span>대화 턴 수</span>
                      <strong>{analysis.end_report.conversation_turns}</strong>
                    </div>
                    {analysis.end_report.key_topics && analysis.end_report.key_topics.length > 0 && (
                      <div className="report-meta">
                        <span>주요 주제</span>
                        <strong>{analysis.end_report.key_topics.join(", ")}</strong>
                      </div>
                    )}
                    <div className="report-guidance">
                      <strong>다음 가이드:</strong> {analysis.end_report.next_guidance}
                    </div>
                  </>
                ) : (
                  // 학생: 친근한 메시지만 표시
                  <div className="report-guidance student-friendly">
                    <p>{analysis.end_report.next_guidance}</p>
                    <p style={{ marginTop: "12px", fontSize: "14px", color: "#666" }}>
                      언제든 다시 대화하고 싶으면 돌아와줘. 항상 여기 있을게.
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <p className="empty">리포트 생성 중...</p>
            )}
          </section>
        )}
      </main>

      {/* 대화 종료 모달 (자살 신호 등으로 종료될 때) */}
      {analysis?.conversation_end && showEndModal && (
        <div
          className="modal-overlay"
          onClick={() => setShowEndModal(false)}
        >
          <div
            className="admin-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="admin-modal-header">
              <h3>여기까지 같이 이야기해줘서 고마워</h3>
              <button
                type="button"
                className="ghost"
                onClick={() => setShowEndModal(false)}
              >
                닫기
              </button>
            </div>
            <div style={{ fontSize: "14px", lineHeight: 1.6, color: "#1f2933" }}>
              <p>
                지금 정말 중요한 이야기를 해줬어. 이제는{" "}
                <strong>어른들이 도와줄 차례야.</strong>
              </p>
              <p style={{ marginTop: "8px" }}>
                응급 상황이면 <strong>112 / 119</strong>, 상담이 필요하면{" "}
                <strong>1388 청소년 상담전화(24시간 무료)</strong>로 바로 연락할 수 있어.
              </p>
              <p style={{ marginTop: "8px", fontSize: "13px", color: "#6b7280" }}>
                이 창은 더 이상 입력을 받지 않고, 지금까지의 대화만 남겨둘게.
              </p>
            </div>
            <div className="admin-links" style={{ marginTop: "16px" }}>
              <button
                type="button"
                className="ghost"
                onClick={() => {
                  // 처음 화면으로 돌아가기
                  setShowEndModal(false);
                  handleReset();
                  setStarted(false);
                  window.history.pushState({ page: "landing" }, "", window.location.href);
                }}
              >
                처음 화면으로 돌아가기
              </button>
              <button
                type="button"
                className="ghost"
                onClick={() => setShowEndModal(false)}
              >
                대화창만 닫기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
