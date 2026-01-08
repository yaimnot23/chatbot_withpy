import os
import sys
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

# 1. 환경설정 로드
load_dotenv()

app = FastAPI(title="University Admission AI Consultant API")

# API 키 확인
if not os.getenv("GOOGLE_API_KEY"):
    print("❌ .env 파일에 GOOGLE_API_KEY가 없습니다.")
    sys.exit()

# 2. 글로벌 리소스 초기화 (서버 시작 시 1회 실행)
db_path = "./db"
embeddings = GoogleGenerativeAIEmbeddings(model="text-embedding-004")
vectorstore = Chroma(persist_directory=db_path, embedding_function=embeddings)

# 대학교 목록 미리 로드
all_metas = vectorstore.get().get('metadatas', [])
univ_list = sorted(list(set([m.get('univ') for m in all_metas if m.get('univ')])))

# 모델 및 프롬프트 설정
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)
system_prompt = (
    "당신은 대한민국 대입 입시 상담 전문 AI입니다. 아래 제공된 [검색된 데이터]를 바탕으로 성심껏 답변하세요.\n\n"
    "[답변 규칙]\n"
    "1. **데이터 기반:** 반드시 제공된 데이터에 있는 내용을 바탕으로 답변하세요.\n"
    "2. **유연한 탐색:** 사용자가 물어본 대학이나 학과 이름이 데이터에 완벽히 일치하지 않더라도, 가장 유사한 정보를 찾아 답변을 시도하세요.\n"
    "3. **수치 명시:** 점수(적정/예상), 모집인원, 지역 등의 정보를 구체적으로 언급하세요.\n"
    "4. **부재 시 대안:** 만약 요청한 학과의 데이터가 정말 없다면, 동일 대학의 유사 학과 정보를 보여주며 대안을 제시하는 등 최대한 도움을 주세요.\n"
    "6. **데이터 정제 (중요):** 모든 수치 데이터는 가독성 좋게 정리하여 답변하세요.\n"
    "    - 현재 제공된 데이터는 **2026학년도 대입(2025년 11월 수능 기준)** 정보입니다. 절대 '20XX'와 같은 임시 표기를 사용하지 말고 정확히 '2026학년도'라고 명시하세요.\n"
    "    - 점수(적정 점수, 예상 점수 등)는 소수점 첫째 자리까지만 반올림하여 표기하세요. (예: 697.37... -> 697.4)\n"
    "    - 인원수(모집 정원 등)는 소수점을 버리고 정수로만 표기하세요. (예: 15.0 -> 15)\n\n"
    "[검색된 데이터]:\n{context}"
)
prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

# 3. 데이터 모델 정의
class ChatRequest(BaseModel):
    query: str
    history: List[dict] = [] # [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

class ChatResponse(BaseModel):
    answer: str
    detected_univ: Optional[str] = None
    found_majors: List[str] = []

# 4. API 엔드포인트 구현
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    user_input = request.query.strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="질문 내용을 입력해주세요.")

    try:
        # [지능형 검색] 대학교 이름 찾기
        matches = []
        for u in univ_list:
            u_short = u.replace("대학교", "")
            if u in user_input: matches.append((u, len(u)))
            elif len(u_short) >= 2 and u_short in user_input: matches.append((u, len(u_short)))
        
        search_kwargs = {"k": 30}
        target_univ = None
        if matches:
            matches.sort(key=lambda x: x[1], reverse=True)
            target_univ = matches[0][0]
            search_kwargs["filter"] = {"univ": target_univ}
            search_kwargs["k"] = 100

        # 검색 실행
        relevant_docs = vectorstore.similarity_search(user_input, **search_kwargs)
        found_majors = sorted(list(set([d.metadata.get('major') for d in relevant_docs])))
        
        # 히스토리 구성
        history_messages = []
        for msg in request.history:
            if msg.get("role") == "user":
                history_messages.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                history_messages.append(AIMessage(content=msg.get("content", "")))
        
        # AI 답변 생성
        messages = prompt_template.format_messages(
            context=context_text, 
            input=user_input,
            history=history_messages
        )
        response = llm.invoke(messages)
        
        # 답변 파싱 (리스트 형태 대응)
        if isinstance(response.content, list):
            final_answer = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in response.content])
        else:
            final_answer = str(response.content)

        return ChatResponse(
            answer=final_answer.strip(),
            detected_univ=target_univ,
            found_majors=found_majors[:15] # 상위 15개 학과만 정보로 제공
        )

    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg.upper():
            raise HTTPException(status_code=429, detail="API 호출 한도가 초과되었습니다. 잠시 후 다시 시도해주세요.")
        raise HTTPException(status_code=500, detail=f"서버 오류 발생: {err_msg}")

@app.get("/health")
async def health_check():
    return {"status": "ok", "university_count": len(univ_list)}

if __name__ == "__main__":
    import uvicorn
    # Hugging Face는 기본적으로 7860 포트를 사용합니다.
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
