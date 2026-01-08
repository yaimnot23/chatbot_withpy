# 04. 멀티턴 대화(기억력) 구현 가이드

이 문서는 챗봇이 이전 대화의 맥락을 기억하여 답변할 수 있도록 구현된 방식과, 연동을 위한 규격을 설명합니다.

---

## 1. 구현 원리 (Mechanism)

챗봇의 '기억력'은 서버가 상태를 저장하는 방식이 아니라, **클라이언트(웹 브라우저)가 대화 내역 전체를 요청 시마다 서버에 전달**하는 상태 비보존(Stateless) 방식으로 구현되었습니다.

1.  **클라이언트**: 대화가 오갈 때마다 JS 배열에 메시지를 쌓아둡니다.
2.  **API 요청**: 다음 질문을 보낼 때, 지금까지의 대화 내역(`history`)을 JSON에 포함하여 전송합니다.
3.  **AI 서버**: 전달받은 `history`를 LLM의 프롬프트 중간에 삽입하여, 이전 맥락을 파악한 뒤 답변을 생성합니다.

---

## 2. API 통신 규격 (JSON)

### Request Payload

`POST /chat` 호출 시 `history` 필드를 포함해야 합니다.

```json
{
  "query": "그럼 그 학과의 정원은 몇 명이야?",
  "history": [
    {
      "role": "user",
      "content": "성균관대 글로벌리더학부에 대해 알려줘."
    },
    {
      "role": "assistant",
      "content": "성균관대 글로벌리더학부는... (상세 답변)"
    }
  ]
}
```

---

## 3. 구성 요소별 변경 사항

### [Python AI Server]

- `server.py`: Pydantic 모델에 `history` 필드 추가.
- `MessagesPlaceholder`를 사용하여 LLM에게 과거 대화 전달.

### [Spring Boot - 향후 작업 필요]

- `ChatbotDTO.java`: `Request` 내부에 `List<Map<String, String>> history` 필드 추가.
- `chatbot.html (JS)`:
  ```javascript
  let chatHistory = [];
  // 메시지 보낼 때마다 push
  chatHistory.push({ role: "user", content: text });
  // 응답 오면 push
  chatHistory.push({ role: "assistant", content: data.answer });
  ```

---

## 4. 장점

- **맥락 이해**: "그 학과는?", "거기는?" 같은 지시 대명사를 완벽하게 이해합니다.
- **서버 리소스 무관**: 서버에서 수만 명의 대화 세션을 메모리에 들고 있지 않아도 되므로 서버가 가볍고 안정적입니다.
