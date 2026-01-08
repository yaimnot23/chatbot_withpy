# 🎓 대입 상담 챗봇 개발 및 문제 해결 과정 요약

본 문서는 LangChain, Chroma, Google Gemini API를 활용한 대입 입시 상담 챗봇 개발 과정에서 발생한 주요 문제와 해결 방안, 그리고 최종 구현된 기능을 정리합니다.

## 1. 프로젝트 개요

- **목표**: 1만 개 이상의 엑셀 입시 데이터를 바탕으로 대학별/학과별 상세 정보를 제공하는 RAG(Retrieval-Augmented Generation) 챗봇 구현.
- **주요 기술**: Python, LangChain, Chroma (Vector DB), Google Generative AI (Gemini Flash).

---

## 2. 주요 문제 해결 (Issue Tracking)

### ① 라이브러리 및 환경 설정 이슈

- **ModuleNotFoundError (langchain.chains)**:
  - **원인**: LangChain 1.x 버전 업데이트로 인해 기존 체인들이 `langchain-classic` 패키지로 분리됨.
  - **해결**: `langchain-classic`, `langchain-community` 설치 및 `from langchain_classic.chains import ...`로 import 구문 수정.
- **NumPy 버전 충돌**:
  - **원인**: NumPy 2.x 버전과 SciPy/NLTK 간의 호환성 문제로 `AttributeError` 발생.
  - **해결**: `pip install "numpy<2.0.0"` 명령으로 안정적인 1.x 버전으로 다운그레이드.

### ② 모델 호출 에러 (Gemini API)

- **404 NOT_FOUND**:
  - **원인**: 사용 중인 API 키에서 지원하지 않는 구형 모델명(`gemini-1.5-flash`) 사용.
  - **해결**: 지원 가능한 `gemini-flash-latest`로 모델명 변경.
- **429 RESOURCE_EXHAUSTED (할당량 초과)**:
  - **원인**: 무료 티어의 분당/일일 호출 한도 초과.
  - **해결**:
    - `ingest.py`: 데이터 저장 시 지수 백오프(Exponential Backoff) 재시도 로직 추가.
    - `main.py`: 사용자에게 할당량 초과에 대한 안내 메시지를 출력하도록 예외 처리.

---

## 3. 검색 성능 및 품질 최적화

### ① 지능형 대학교 인식 시스템

- **문제**: 질문 속의 특정 단어(예: '국제'학과)를 대학교 이름으로 오해하여 엉뚱한 학교 정보를 가져옴.
- **해결**: 질문에서 가장 길게 매칭되는 대학교 이름을 우선 선택하는 로직을 도입하여 인식 정확도 향상. (예: '성결대학교 국제학과' 질문 시 '성결대학교'를 우선 인식)

### ② 정밀 타겟 검색 (Metadata Filtering)

- **문제**: 1만 개가 넘는 방대한 데이터 사이에서 비슷한 지역의 다른 대학 정보들이 섞여 들어옴.
- **해결**: 질문에서 대학교가 감지되면, DB 검색 단계에서 해당 대학교의 데이터만 필터링하도록 `where` 필터 적용.

### ③ 대규모 데이터 처리 (Search Volume 확대)

- **문제**: 학과가 매우 많은 대학(예: 인천대)은 상위 30개 검색만으로 모든 정보를 담기 부족함.
- **해결**: 대학교 검색 시 검색 수(`k`)를 최대 100개까지 확대하고, 다양성을 확보하기 위해 **MMR(Maximal Marginal Relevance)** 검색 방식 적용.

---

## 4. 사용자 경험 (UX) 및 보안

### ① 출력 데이터 정제

- **문제**: AI 답변 뒤에 `extras`, `signature` 등 개발용 메타데이터가 함께 출력됨.
- **해결**: AI 응답 객체에서 `content`만 추출하고, 리스트 형식의 응답도 깔끔하게 텍스트로 변환하는 파싱 로직 강화.

### ② 보안 및 Git 설정

- **.gitignore 설정**: API 키(`*.env`), 로컬 데이터베이스(`db/`), 파이썬 가상환경(`.venv/`) 등이 실수로 공유되지 않도록 설정 파일 생성.

---

## 5. 실행 방법 리마인드

1. **데이터 인덱싱**: `python ingest.py` (최초 1회 및 데이터 변경 시)
2. **챗봇 실행**: `python main.py`

---

_문서 생성 시점: 2026년 1월 7일_
