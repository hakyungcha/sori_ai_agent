import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "";

export default function AdminPage({ onBack, onLogout }) {
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("dashboard"); // dashboard, test
  const [pageByTab, setPageByTab] = useState({ dashboard: 1, test: 1 });
  const itemsPerPage = 10;

  useEffect(() => {
    // activeTab에 따라 다른 대화 목록 로드
    if (activeTab === "test") {
      loadConversations(true); // 테스트 대화 포함
    } else {
      loadConversations(false); // 일반 대화만
    }
    setPageByTab((prev) => ({ ...prev, [activeTab]: 1 }));
  }, [activeTab]);

  const paginate = (items, page) => {
    const start = (page - 1) * itemsPerPage;
    return items.slice(start, start + itemsPerPage);
  };

  const renderPagination = (totalItems, currentPage, onChange) => {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    if (totalPages <= 1) return null;
    return (
      <div style={{ display: "flex", gap: "8px", marginTop: "16px", flexWrap: "wrap" }}>
        {Array.from({ length: totalPages }, (_, idx) => {
          const page = idx + 1;
          const isActive = page === currentPage;
          return (
            <button
              key={page}
              type="button"
              onClick={() => onChange(page)}
              style={{
                minWidth: "32px",
                height: "32px",
                borderRadius: "8px",
                border: isActive ? "1px solid #1e3a5f" : "1px solid #e5e5e5",
                background: isActive ? "#1e3a5f" : "white",
                color: isActive ? "white" : "#1e3a5f",
                cursor: "pointer",
                fontSize: "13px",
              }}
            >
              {page}
            </button>
          );
        })}
      </div>
    );
  };

  const loadConversations = async (includeTest = false) => {
    try {
      setLoading(true);
      const url = `${API_BASE}/api/admin/conversations${includeTest ? '?include_test=true' : ''}`;
      const response = await fetch(url);
      if (!response.ok) throw new Error("대화 목록을 불러올 수 없습니다.");
      const data = await response.json();
      setConversations(data.conversations || []);
    } catch (err) {
      setError(err.message || "오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const loadConversationDetail = async (filename) => {
    try {
      setLoading(true);
      // 파일명으로 테스트 여부 판단
      const isTest = filename.startsWith("test_");
      const url = `${API_BASE}/api/admin/conversations/${filename}${isTest ? '?is_test=true' : ''}`;
      const response = await fetch(url);
      if (!response.ok) throw new Error("대화를 불러올 수 없습니다.");
      const data = await response.json();
      setSelectedConversation(data);
    } catch (err) {
      setError(err.message || "오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // 사이드바 메뉴 컴포넌트
  const Sidebar = ({ currentTab, onTabChange, onLogout }) => (
    <aside style={{ 
      width: "200px", 
      flexShrink: 0,
      display: "flex",
      flexDirection: "column",
      gap: "8px"
    }}>
      <button
        type="button"
        onClick={() => {
          setSelectedConversation(null);
          onTabChange("dashboard");
        }}
        style={{
          padding: "16px",
          background: currentTab === "dashboard" ? "#1e3a5f" : "#f8fafc",
          color: currentTab === "dashboard" ? "white" : "#1e3a5f",
          border: "none",
          borderRadius: "12px",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          gap: "12px",
          fontSize: "15px",
          fontWeight: currentTab === "dashboard" ? "600" : "400",
          transition: "all 0.2s",
        }}
        onMouseEnter={(e) => {
          if (currentTab !== "dashboard") {
            e.currentTarget.style.background = "#e8f2ff";
          }
        }}
        onMouseLeave={(e) => {
          if (currentTab !== "dashboard") {
            e.currentTarget.style.background = "#f8fafc";
          }
        }}
      >
        <span style={{ fontSize: "20px" }}>📊</span>
        <span>대시보드</span>
      </button>
      <button
        type="button"
        onClick={() => {
          setSelectedConversation(null);
          onTabChange("test");
        }}
        style={{
          padding: "16px",
          background: currentTab === "test" ? "#1e3a5f" : "#f8fafc",
          color: currentTab === "test" ? "white" : "#1e3a5f",
          border: "none",
          borderRadius: "12px",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          gap: "12px",
          fontSize: "15px",
          fontWeight: currentTab === "test" ? "600" : "400",
          transition: "all 0.2s",
        }}
        onMouseEnter={(e) => {
          if (currentTab !== "test") {
            e.currentTarget.style.background = "#e8f2ff";
          }
        }}
        onMouseLeave={(e) => {
          if (currentTab !== "test") {
            e.currentTarget.style.background = "#f8fafc";
          }
        }}
      >
        <span style={{ fontSize: "20px" }}>🧪</span>
        <span>테스트</span>
      </button>
      <button
        type="button"
        onClick={() => {
          if (onLogout) {
            onLogout();
          }
        }}
        style={{
          padding: "16px",
          background: "#fee2e2",
          color: "#dc2626",
          border: "none",
          borderRadius: "12px",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          gap: "12px",
          fontSize: "15px",
          fontWeight: "500",
          marginTop: "auto",
          transition: "all 0.2s",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = "#fecaca";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = "#fee2e2";
        }}
      >
        <span style={{ fontSize: "20px" }}>🚪</span>
        <span>로그아웃</span>
      </button>
    </aside>
  );

  // 대화 상세 화면
  if (selectedConversation) {
    return (
      <div className="admin-page">
        <header className="header">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
              <button
                type="button"
                onClick={() => setSelectedConversation(null)}
                className="ghost"
              >
                ← 목록으로
              </button>
              <div>
                <h1>대화 상세</h1>
                <p>
                  {selectedConversation.date} {selectedConversation.time}
                </p>
              </div>
            </div>
          </div>
        </header>

        <div style={{ 
          display: "flex", 
          gap: "24px", 
          padding: "24px", 
          maxWidth: "1200px", 
          margin: "0 auto" 
        }}>
          <Sidebar 
            currentTab={activeTab} 
            onTabChange={setActiveTab}
            onLogout={onLogout}
          />

          <main style={{ flex: 1 }}>
            <div className="panel" style={{ marginBottom: "18px" }}>
              <h2>대화 내용</h2>
              <div className="chat-window" style={{ maxHeight: "400px", overflowY: "auto" }}>
                {selectedConversation.history?.map((turn, index) => (
                  <div
                    key={index}
                    className={`message-wrapper ${turn.role}`}
                    style={{ marginBottom: "12px" }}
                  >
                    <div className={`bubble ${turn.role}`}>
                      <p>{turn.content}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="panel" style={{ marginBottom: "18px" }}>
              <h2>분석 결과</h2>
              <div className="status">
                <div>
                  <span>정서적 고통</span>
                  <strong>{selectedConversation.analysis?.emotional_distress}</strong>
                </div>
                <div>
                  <span>자살 신호</span>
                  <strong>{selectedConversation.analysis?.suicide_signal}</strong>
                </div>
                <div>
                  <span>위험 점수</span>
                  <strong>{selectedConversation.analysis?.risk_score}</strong>
                </div>
                <div>
                  <span>다음 조치</span>
                  <strong>{selectedConversation.analysis?.next_action}</strong>
                </div>
              </div>
            </div>

            {selectedConversation.end_report && (
              <div className="panel" style={{ marginBottom: "18px" }}>
                <h2>종합 리포트</h2>
                <div className="report">
                  <p><strong>대화 요약:</strong> {selectedConversation.end_report.summary}</p>
                  <div className="report-meta">
                    <span>최종 위험 점수</span>
                    <strong>{selectedConversation.end_report.risk_score}</strong>
                  </div>
                  <div className="report-meta">
                    <span>상태 추이</span>
                    <strong>{selectedConversation.end_report.trend}</strong>
                  </div>
                  <div className="report-meta">
                    <span>정서적 고통</span>
                    <strong>{selectedConversation.end_report.distress_level}</strong>
                  </div>
                  <div className="report-meta">
                    <span>자살 신호</span>
                    <strong>{selectedConversation.end_report.suicide_signal}</strong>
                  </div>
                  <div className="report-meta">
                    <span>대화 턴 수</span>
                    <strong>{selectedConversation.end_report.conversation_turns}</strong>
                  </div>
                  {selectedConversation.end_report.key_topics?.length > 0 && (
                    <div className="report-meta">
                      <span>주요 주제</span>
                      <strong>{selectedConversation.end_report.key_topics.join(", ")}</strong>
                    </div>
                  )}
                  <div className="report-guidance">
                    <strong>다음 가이드:</strong> {selectedConversation.end_report.next_guidance}
                  </div>
                </div>
              </div>
            )}

            <div className="panel">
              <h2>JSON 출력</h2>
              <div className="json-output">
                <pre>{JSON.stringify(selectedConversation, null, 2)}</pre>
              </div>
            </div>
          </main>
        </div>
      </div>
    );
  }

  // 메인 대시보드 화면
  return (
    <div className="admin-page">
      <header className="header">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <button type="button" onClick={onBack} className="ghost">
              ← 뒤로 가기
            </button>
            <div>
              <h1>관리자 대시보드</h1>
              <p>저장된 대화 목록 및 테스트</p>
            </div>
          </div>
        </div>
      </header>

      <div style={{ 
        display: "flex", 
        gap: "24px", 
        padding: "24px", 
        maxWidth: "1200px", 
        margin: "0 auto" 
      }}>
        <Sidebar 
          currentTab={activeTab} 
          onTabChange={setActiveTab}
          onLogout={onLogout}
        />

        <main style={{ flex: 1 }}>
          {activeTab === "test" ? (
            <>
              {loading ? (
                <div className="panel">
                  <p>로딩 중...</p>
                </div>
              ) : error ? (
                <div className="panel">
                  <p className="error">{error}</p>
                  <button type="button" onClick={() => loadConversations(true)}>
                    다시 시도
                  </button>
                </div>
              ) : conversations.filter(conv => conv.is_test).length === 0 ? (
                <div className="panel">
                  <h2>🧪 테스트 대화 목록</h2>
                  <p className="empty" style={{ marginTop: "12px" }}>
                    저장된 테스트 대화가 없습니다. 관리자 모드로 로그인한 후 대화를 진행하면 여기에 저장됩니다.
                  </p>
                </div>
              ) : (
                <div className="panel">
                  <h2>테스트 대화 목록 ({conversations.filter(conv => conv.is_test).length}개)</h2>
                  <div style={{ display: "grid", gap: "12px", marginTop: "16px" }}>
                    {paginate(
                      conversations.filter(conv => conv.is_test),
                      pageByTab.test
                    ).map((conv) => (
                        <div
                          key={conv.filename}
                          onClick={() => loadConversationDetail(conv.filename)}
                          style={{
                            padding: "16px",
                            border: "1px solid #e5e5e5",
                            borderRadius: "12px",
                            cursor: "pointer",
                            transition: "all 0.2s",
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = "#f8fafc";
                            e.currentTarget.style.borderColor = "#1e3a5f";
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = "white";
                            e.currentTarget.style.borderColor = "#e5e5e5";
                          }}
                        >
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                            <div>
                              <div style={{ fontWeight: "bold", marginBottom: "4px" }}>
                                {conv.date} {conv.time}
                              </div>
                              <div style={{ fontSize: "14px", color: "#666", marginBottom: "8px" }}>
                                {conv.summary}
                              </div>
                              <div style={{ display: "flex", gap: "16px", fontSize: "12px", color: "#888" }}>
                                <span>위험 점수: {conv.risk_score}</span>
                                <span>정서적 고통: {conv.distress_level}</span>
                              </div>
                            </div>
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                loadConversationDetail(conv.filename);
                              }}
                              style={{
                                padding: "6px 12px",
                                background: "#1e3a5f",
                                color: "white",
                                border: "none",
                                borderRadius: "6px",
                                cursor: "pointer",
                                fontSize: "12px",
                              }}
                            >
                              상세 보기
                            </button>
                          </div>
                        </div>
                      ))}
                  </div>
                  {renderPagination(
                    conversations.filter(conv => conv.is_test).length,
                    pageByTab.test,
                    (page) => setPageByTab((prev) => ({ ...prev, test: page }))
                  )}
                </div>
              )}
            </>
          ) : (
            <>
              {loading ? (
                <div className="panel">
                  <p>로딩 중...</p>
                </div>
              ) : error ? (
                <div className="panel">
                  <p className="error">{error}</p>
                  <button type="button" onClick={() => loadConversations(false)}>
                    다시 시도
                  </button>
                </div>
              ) : conversations.filter(conv => !conv.is_test).length === 0 ? (
                <div className="panel">
                  <p className="empty">저장된 대화가 없습니다.</p>
                </div>
              ) : (
                <div className="panel">
                  <h2>대화 목록 ({conversations.filter(conv => !conv.is_test).length}개)</h2>
                  <div style={{ display: "grid", gap: "12px", marginTop: "16px" }}>
                    {paginate(
                      conversations.filter(conv => !conv.is_test),
                      pageByTab.dashboard
                    ).map((conv) => (
                        <div
                          key={conv.filename}
                          onClick={() => loadConversationDetail(conv.filename)}
                          style={{
                            padding: "16px",
                            border: "1px solid #e5e5e5",
                            borderRadius: "12px",
                            cursor: "pointer",
                            transition: "all 0.2s",
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = "#f8fafc";
                            e.currentTarget.style.borderColor = "#1e3a5f";
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = "white";
                            e.currentTarget.style.borderColor = "#e5e5e5";
                          }}
                        >
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                            <div>
                              <div style={{ fontWeight: "bold", marginBottom: "4px" }}>
                                {conv.date} {conv.time}
                              </div>
                              <div style={{ fontSize: "14px", color: "#666", marginBottom: "8px" }}>
                                {conv.summary}
                              </div>
                              <div style={{ display: "flex", gap: "16px", fontSize: "12px", color: "#888" }}>
                                <span>위험 점수: {conv.risk_score}</span>
                                <span>정서적 고통: {conv.distress_level}</span>
                              </div>
                            </div>
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                loadConversationDetail(conv.filename);
                              }}
                              style={{
                                padding: "6px 12px",
                                background: "#1e3a5f",
                                color: "white",
                                border: "none",
                                borderRadius: "6px",
                                cursor: "pointer",
                                fontSize: "12px",
                              }}
                            >
                              상세 보기
                            </button>
                          </div>
                        </div>
                      ))}
                  </div>
                  {renderPagination(
                    conversations.filter(conv => !conv.is_test).length,
                    pageByTab.dashboard,
                    (page) => setPageByTab((prev) => ({ ...prev, dashboard: page }))
                  )}
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
