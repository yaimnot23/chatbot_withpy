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
    "당신은 대한민국 최고의 대입 입시 전문 AI 컨설턴트입니다. **현재 날짜는 2026년 1월 8일이며, 당신이 상담하는 모든 데이터는 2026학년도 대입(2025년 11월 수능) 기준입니다.**\n\n"
    "[상담 가이드라인]\n"
    "1. **전문 분야 한정:** 당신은 오직 '대학교 입시', '진학 상담', '성적 진단'과 관련된 질문에만 답변합니다. **입시나 성적과 전혀 관련 없는 질문(예: 요리 레시피, 일반 상식, 일상 대화 등)에 대해서는 \"죄송합니다. 저는 대입 입시 및 성적 상담 전문 AI 컨설턴트로, 해당 질문에는 답변을 드릴 수 없습니다.\"라고 정중히 거절하세요.**\n"
    "2. **학습 데이터 활용:** 지식(Context)에 `### [시스템 내부 성적 진단 보고서]`가 포함되어 있다면, 이를 바탕으로 개인화된 합격 가능성을 즉시 진단하세요. 보고서가 없다면 객관적 데이터 위주로 상담하세요.\n"
    "3. **계산 금지 지침:** 보고서가 있을 경우, 이미 계산된 결과를 최우선으로 신뢰하고 직접 계산하지 마세요.\n"
    "4. **확신 있는 판정:** [안정/적정/소신/불가] 판정을 명확히 말하고, Gap Analysis를 제시하세요.\n"
    "5. **데이터 가독성:** 점수는 소수점 첫째 자리까지, 정원은 정수로 표기하세요.\n\n"
    "[사용자별 전문 진단 보고서 및 입시 데이터]:\n{context}"
)
prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

# 3. 데이터 모델 정의
class UserScore(BaseModel):
    subjectName: str
    score: int
    scoreType: str
    category: str

class ChatRequest(BaseModel):
    query: str
    history: List[dict] = []
    userScores: Optional[List[UserScore]] = None
    sessionId: Optional[int] = None # 추가

class ChatResponse(BaseModel):
    answer: str
    detected_univ: Optional[str] = None
    found_majors: List[str] = []
    analysis_result: Optional[str] = None
    title: Optional[str] = None # 추가 (새로운 대화 제목)

# 5. 성적 분석 엔진 및 유틸리티
# 표준점수 -> 누적 백분위(%) 매핑 (2026학년도 추정치 기반 샘플 데이터)
SCORE_TO_PERCENTILE = {
    "국어": {145: 0.1, 140: 0.5, 135: 1.5, 130: 4.0, 125: 10.0, 120: 20.0, 115: 35.0, 110: 50.0},
    "수학": {148: 0.1, 140: 0.8, 135: 2.0, 130: 5.0, 125: 12.0, 120: 22.0, 115: 38.0, 110: 55.0},
    "탐구": {75: 0.1, 70: 1.0, 65: 4.0, 60: 12.0, 55: 25.0, 50: 45.0} # 과목별 평균값 기준
}

def get_percentile(subject, score):
    """표준점수를 백분위로 변환 (선형 보간 적용)"""
    table = SCORE_TO_PERCENTILE.get(subject, SCORE_TO_PERCENTILE["탐구"])
    scores = sorted(table.keys(), reverse=True)
    
    if score >= scores[0]: return table[scores[0]]
    if score <= scores[-1]: return table[scores[-1]]
    
    for i in range(len(scores) - 1):
        s1, s2 = scores[i], scores[i+1]
        if s1 >= score > s2:
            p1, p2 = table[s1], table[s2]
            # 선형 보간: p = p1 + (score - s1) * (p2 - p1) / (s2 - s1)
            return p1 + (score - s1) * (p2 - p1) / (s2 - s1)
    return 100.0

def calculate_admission_status(user_percentile, target_percentile):
    """합격 가능성 및 부족 점수 계산 (Gap Analysis)"""
    diff = user_percentile - target_percentile
    if diff <= -1.5: status = "안정"
    elif diff <= 0: status = "적정"
    elif diff <= 1.5: status = "소신"
    else: status = "불가"
    
    # 부족 점수 추정 (약 0.3%p 누백 ≈ 수능 표점 1점 가정)
    gap_score = max(0, round(diff / 0.3)) if status in ["소신", "불가"] else 0
    return status, gap_score

# 6. API 엔드포인트 구현
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
        
        # [추가] 성적 분석 컨텍스트 생성
        analysis_context = ""
        user_total_percentile = None
        
        # 디버깅: 받은 성적 데이터 확인
        print(f"DEBUG: Received userScores count: {len(request.userScores) if request.userScores else 0}")
        
        if request.userScores:
            # 과목별 누백 계산
            scores = {s.subjectName: s.score for s in request.userScores}
            p_kor = get_percentile("국어", scores.get("국어", 0))
            p_mat = get_percentile("수학", scores.get("수학", 0))
            # 사탐/과탐 평균 계산
            inquiry_scores = [s.score for s in request.userScores if s.category in ["사탐", "과탐"]]
            p_inq = sum([get_percentile("탐구", s) for s in inquiry_scores]) / len(inquiry_scores) if inquiry_scores else 50.0
            
            # 대학교 가중치 적용 (데이터 기반 시뮬레이션)
            # 검색된 문서들(relevant_docs) 중 첫 번째 문서의 가중치를 샘플로 사용하거나 고정값 적용
            # 여기서는 분석 로직을 보여주기 위해 context에 분석 결과를 추가함
            
            # 사용자 일반 누백 (가중치 미적용 평균)
            user_total_percentile = (p_kor * 0.3 + p_mat * 0.4 + p_inq * 0.3)
            analysis_context = f"\n### [시스템 내부 성적 진단 보고서]\n"
            analysis_context += f"- **사용자 추정 누적 백분위**: 상위 {user_total_percentile:.2f}%\n"
            
            # 대학 탐지 시 합격 진단 추가
            if target_univ:
                # 검색된 메타데이터에서 누백(target) 및 비중(weights) 추출 시도
                target_per = 2.0  # 기본값
                weights = {"국어": 0.3, "수학": 0.4, "탐구": 0.3} # 기본 비중
                
                for d in relevant_docs:
                    if d.metadata.get('univ') == target_univ:
                        try:
                            t_raw = d.metadata.get('누백')
                            if t_raw and t_raw != "": target_per = float(t_raw)
                            
                            w_kor = d.metadata.get('국어비중')
                            w_mat = d.metadata.get('수학비중')
                            w_inq = d.metadata.get('탐구비중')
                            if w_kor: weights["국어"] = float(w_kor)
                            if w_mat: weights["수학"] = float(w_mat)
                            if w_inq: weights["탐구"] = float(w_inq)
                            break
                        except: continue
                
                # 가중치 적용 누백 재계산
                user_total_percentile = (p_kor * weights["국어"] + p_mat * weights["수학"] + p_inq * weights["탐구"])
                analysis_context = f"\n### [시스템 내부 성적 진단 보고서 - {target_univ} 기준]\n"
                analysis_context += f"- **{target_univ} 맞춤형 누백**: 상위 {user_total_percentile:.2f}%\n"
                
                status, gap = calculate_admission_status(user_total_percentile, target_per)
                analysis_context += f"- **최종 합격 진단**: [{status}] (적정 합격선: 상위 {target_per}%)\n"
                if gap > 0:
                    analysis_context += f"- **성적 향상 목표 (Gap Analysis)**: 수능 표준점수 총점 기준 약 {gap}점 추가 확보 필요\n"
                else:
                    analysis_context += f"- **전문가 조언**: 현재 성적을 유지하신다면 {target_univ} 합격 가능성이 매우 높습니다.\n"
            
            analysis_context += "--------------------------------------------------\n"

        # 컨텍스트 구성
        context_text = analysis_context + "\n\n" + "\n\n".join([d.page_content for d in relevant_docs])
        
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

        # [추가] 제목 자동 생성 로직 (첫 대화일 경우에만)
        new_title = None
        if not request.history and not any(msg for msg in history_messages):
            try:
                title_prompt = (
                    "당신은 대화 제목 요약 전문가입니다. 아래 사용자의 질문을 분석하여 15자 내외의 명사형 제목으로 요약하세요.\n"
                    "예: '서울대 경영학과 합격선 알려줘' -> '서울대 경영학과 입시 문의'\n"
                    "예: '내 성적으로 어디 갈 수 있어?' -> '사용자 맞춤 성적 진단'\n\n"
                    f"질문: {user_input}\n"
                    "제목:"
                )
                title_response = llm.invoke(title_prompt)
                new_title = str(title_response.content).strip().replace('"', '').replace("'", "")
            except Exception as e:
                print(f"DEBUG: Title generation failed: {e}")
                new_title = user_input[:15] + "..." if len(user_input) > 15 else user_input

        return ChatResponse(
            answer=final_answer.strip(),
            detected_univ=target_univ,
            found_majors=found_majors[:15],
            title=new_title # 제목 반환
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
