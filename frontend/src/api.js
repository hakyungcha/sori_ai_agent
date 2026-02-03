const API_BASE = import.meta.env.VITE_API_BASE || "";

export async function sendChat(payload, isAdmin = false) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => {
    controller.abort();
  }, 60000); // 타임아웃 60초로 증가 (LLM 응답이 오래 걸릴 수 있음)
  
  try {
    // 관리자 모드 정보 추가
    const requestPayload = {
      ...payload,
      is_admin: isAdmin
    };
    
    const response = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestPayload),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`서버 오류 (${response.status}): ${errorText || "알 수 없는 오류"}`);
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error.name === "AbortError" || error.message?.includes("aborted")) {
      throw new Error("요청 시간이 초과되었습니다. 백엔드 서버가 실행 중인지 확인해주세요. (http://localhost:8000)");
    }
    
    // 네트워크 에러
    if (error.message?.includes("Failed to fetch") || error.message?.includes("NetworkError")) {
      throw new Error("서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.");
    }
    
    if (error.message) {
      throw error;
    }
    
    throw new Error(`통신 오류: ${error.message || "알 수 없는 오류가 발생했습니다."}`);
  }
}
