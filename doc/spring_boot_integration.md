# Spring Boot 연동 가이드 (Python API Server)

파이썬으로 만든 AI 서버(`server.py`)를 Spring Boot 프로젝트에서 호출하는 방법입니다.

## 1. 파이썬 서버 실행

먼저 터미널에서 서버를 실행합니다:

```bash
python server.py
```

서버는 기본적으로 `http://localhost:8000`에서 대기합니다.

---

## 2. Spring Boot에서 호출하기 (RestTemplate 예제)

### Request/Response DTO 정의

```java
// 요청 데이터 모델
public class ChatRequest {
    private String query;
    public ChatRequest(String query) { this.query = query; }
    // Getter, Setter 생략
}

// 응답 데이터 모델
public class ChatResponse {
    private String answer;
    private String detected_univ;
    private List<String> found_majors;
    // Getter, Setter 생략
}
```

### API 호출 서비스 구현

```java
@Service
public class ChatbotService {
    private final RestTemplate restTemplate = new RestTemplate();
    private final String AI_SERVER_URL = "http://localhost:8000/chat";

    public String getChatResponse(String userMessage) {
        ChatRequest request = new ChatRequest(userMessage);

        try {
            ChatResponse response = restTemplate.postForObject(AI_SERVER_URL, request, ChatResponse.class);
            return response.getAnswer();
        } catch (Exception e) {
            return "AI 서버와 통신 중 에러가 발생했습니다: " + e.getMessage();
        }
    }
}
```

---

## 3. 주요 API 엔드포인트 정보

- **상태 확인 (GET)**: `http://localhost:8000/health`
  - 서버가 잘 작동하는지 확인할 수 있습니다.
- **채팅 (POST)**: `http://localhost:8000/chat`
  - Body: `{"query": "성균관대 정보 알려줘"}`
  - Result: AI 답변과 검색된 대학/학과 리스트를 포함한 JSON 반환.

---

## 4. 이점

- **UI 자유도**: Spring Boot가 받은 답변 텍스트를 웹 채팅창(HTML/JS)에 맞게 가공하여 표나 리스트로 예쁘게 보여줄 수 있습니다.
- **비즈니스 로직**: 사용자의 질문 이력을 DB(MariaDB/MySQL 등)에 저장하고 관리하기에 용이합니다.
