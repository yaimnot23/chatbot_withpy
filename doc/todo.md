나는 Python과 LangChain, Google Gemini API를 활용해서 'AI 대학 입시 컨설턴트 챗봇'을 만들고 싶어.
아래의 [프로젝트 환경]과 [상세 요구사항]을 반영하여 **완벽하게 동작하는 파이썬 코드 2개(`ingest.py`, `main.py`)와 설치 명령어**를 작성해줘.

### [프로젝트 환경]

1. **데이터 위치:** `data/univer_data.xlsx` (파일 하나에 '문과', '이과' 등 여러 시트가 존재함)
2. **기술 스택:**
   - LangChain (최신 버전, langchain-chroma 사용)
   - ChromaDB (벡터 데이터베이스)
   - Google Gemini API (`gemini-1.5-flash` 모델)
   - Embeddings: `models/text-embedding-004` (최신 모델 사용)g
   - Python Libraries: `pandas`, `openpyxl`, `tqdm`, `python-dotenv`

### [상세 요구사항]

**1. `ingest.py` (데이터 저장용)**

- `pandas`를 사용해 엑셀 파일 내의 **모든 시트(Sheet)**를 순회하며 데이터를 읽어와줘.
- 데이터가 약 1만 건 이상이므로, Google API의 **Rate Limit(429 Error)를 피하기 위해 다음 로직을 반드시 포함해줘**:
  - `tqdm`을 사용하여 진행률을 보여줄 것.
  - 데이터를 **30개씩 Batch(묶음)**로 나누어 처리할 것.
  - 각 Batch 처리가 끝날 때마다 `time.sleep(1.5)`를 넣어 1.5초씩 쉴 것.
- 기존 `./db` 폴더가 있다면 삭제하고 새로 만드는 로직을 추가해줘.
- 엑셀의 NaN(빈 값) 데이터는 에러가 나지 않도록 빈 문자열이나 "정보없음"으로 처리해줘.

**2. `main.py` (챗봇 실행용)**

- 저장된 ChromaDB를 불러와서 RAG(검색 증강 생성) 챗봇을 구현해줘.
- **System Prompt:** "당신은 입시 상담 AI입니다. 데이터를 기반으로 수치를 정확하게 답변하고, 출처(대학/학과)를 명시하세요."
- 사용자가 터미널에서 계속 대화할 수 있도록 `while` 루프로 구현해줘. ('exit' 입력 시 종료)
- 에러 발생 시 프로그램이 꺼지지 않고 에러 메시지만 출력하고 계속 대화가 가능하도록 예외 처리를 해줘.

**3. 추가 요청**

- 실행에 필요한 모든 라이브러리를 한 번에 설치할 수 있는 `pip install` 명령어를 가장 먼저 알려줘.
- 코드는 복사해서 바로 실행할 수 있도록 주석을 달아줘.
