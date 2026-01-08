import os
import sys
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# 1. 환경설정 로드(env에서)
load_dotenv()

def start_chatbot():
    # API 키 확인
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ .env 파일에 GOOGLE_API_KEY가 없습니다.")
        sys.exit()

    # 2. DB 및 대학교 목록 불러오기
    db_path = "./db"
    if not os.path.exists(db_path):
        print(f"❌ '{db_path}' 폴더가 없습니다. 'python ingest.py'를 먼저 실행하여 데이터를 인덱싱해주세요!")
        sys.exit()

    print("🔍 시스템 초기화 중...")
    try:
        # 임베딩 모델 설정
        embeddings = GoogleGenerativeAIEmbeddings(model="text-embedding-004")
        
        # 벡터 DB 로드
        vectorstore = Chroma(
            persist_directory=db_path,
            embedding_function=embeddings
        )

        # 전체 대학 목록 추출 (메타데이터에서 고유값 가져오기)
        # 검색 정확도를 높이기 위해 미리 대학 목록을 알고 있으면 좋습니다.
        print("🎓 대학교 목록 로딩 중...")
        all_metas = vectorstore.get().get('metadatas', [])
        univ_list = sorted(list(set([m.get('univ') for m in all_metas if m.get('univ')])))
        print(f"✅ {len(univ_list)}개의 대학교 정보를 확인했습니다.")

        # 3. 챗봇 설정 (Retriever & LLM)
        # 검색 품질을 높이기 위해 MMR(Maximal Marginal Relevance) 검색방식 사용
        # 100개를 먼저 뽑은 뒤, 그 중 가장 의미가 겹치지 않는 30개를 최종 선정
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={'k': 30, 'fetch_k': 100}
        )
        llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)

        # 4. 시스템 프롬프트 및 체인 설정
        system_prompt = (
            "당신은 대한민국 대입 입시 상담 전문 AI입니다. 아래 제공된 [검색된 데이터]를 바탕으로 성심껏 답변하세요.\n\n"
            "[답변 규칙]\n"
            "1. **데이터 기반:** 반드시 제공된 데이터에 있는 내용을 바탕으로 답변하세요.\n"
            "2. **유연한 탐색:** 사용자가 물어본 대학이나 학과 이름이 데이터에 완벽히 일치하지 않더라도, 가장 유사한 정보를 찾아 답변을 시도하세요. (예: '가천대 의대'를 물었는데 데이터에 '가천대학교 의예과'가 있다면 이를 활용하세요.)\n"
            "3. **수치 명시:** 점수(적정/예상), 모집인원, 지역 등의 정보를 구체적으로 언급하세요.\n"
            "4. **부재 시 대안:** 만약 요청한 학과의 데이터가 정말 없다면, 동일 대학의 유사 학과 정보를 보여주며 대안을 제시하는 등 최대한 도움을 주세요.\n"
            "5. **친절한 말투:** 수험생에게 따뜻한 격려와 함께 전문적인 조언을 건네세요.\n\n"
            "[검색된 데이터]:\n{context}"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

        # 검색-생성(RAG) 체인 생성
        combine_docs_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, combine_docs_chain)

        # 5. 대화 루프
        print("\n" + "="*50)
        print("🎓 AI 대학 입시 컨설턴트 챗봇이 활성화되었습니다!")
        print("질문을 입력하세요. 종료하려면 'exit'를 입력하세요.")
        print("="*50)

        while True:
            user_input = input("\n👤 질문: ").strip()
            
            if user_input.lower() in ["exit", "종료", "quit"]:
                print("👋 입시 상담을 종료합니다. 행운을 빌어요!")
                break
            
            if not user_input:
                continue

            try:
                # [지능형 검색] 사용자의 질문에 포함된 대학교 이름 찾기
                # 단순히 포함 여부만 보는 게 아니라, 질문에서 가장 길게 매칭되는 대학 이름을 선택
                matches = []
                for u in univ_list:
                    u_short = u.replace("대학교", "")
                    if u in user_input:
                        matches.append((u, len(u)))
                    elif len(u_short) >= 2 and u_short in user_input:
                        matches.append((u, len(u_short)))
                
                # 가장 길게 매칭된 대학을 선택 (예: '성결대학교 국제학과' -> '국제'보다 '성결대학교' 우선)
                search_kwargs = {"k": 30}
                if matches:
                    matches.sort(key=lambda x: x[1], reverse=True)
                    target_univ = matches[0][0]
                    search_kwargs["filter"] = {"univ": target_univ}
                    search_kwargs["k"] = 100
                    print(f"🎯 '{target_univ}' 필터링 검색을 수행합니다 (최대 100개)...")
                else:
                    print("🔍 일반 검색을 수행합니다...")

                # 1. 문서 검색
                relevant_docs = vectorstore.similarity_search(user_input, **search_kwargs)
                
                # 2. 검색 결과 로그 (어떤 전공들이 검색되었는지 출력)
                found_majors = sorted(list(set([d.metadata.get('major') for d in relevant_docs])))
                found_univs = sorted(list(set([d.metadata.get('univ') for d in relevant_docs])))
                print(f"✅ 검색된 대학: {found_univs}")
                print(f"✅ 검색된 전공(일부): {found_majors[:10]}... (총 {len(found_majors)}개 학과)")

                # 3. 컨텍스트 구성
                doc_contents = [d.page_content for d in relevant_docs]
                context_text = "\n\n".join(doc_contents)
                
                # 4. 프롬프트 생성 및 실행
                messages = prompt.format_messages(context=context_text, input=user_input)
                response = llm.invoke(messages)
                
                # 5. 답변 출력 (리스트 형식의 응답도 텍스트만 추출하도록 개선)
                if isinstance(response.content, list):
                    # 리스트 내의 각 항목에서 'text' 키의 값만 합침
                    final_answer = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in response.content])
                else:
                    final_answer = str(response.content)
                
                print(f"\n🤖 AI 답변: {final_answer.strip()}")
                
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg.upper():
                    print("\n⚠️ API 호출 한도 초과 (429 Error):")
                    print("현재 사용 중인 Gemini API의 무료 티어 할당량을 모두 소진했습니다.")
                    print("약 1분~1시간 뒤에 다시 시도하거나, 다른 API 키를 사용해야 합니다.")
                else:
                    print(f"\n❌ 답변 도중 에러가 발생했습니다: {err_msg}")
                print("잠시 후 다시 시도해주세요.")

    except Exception as e:
        print(f"❌ 시스템 초기화 중 오류 발생: {e}")

if __name__ == "__main__":
    start_chatbot()
