# 🛠️ Chatbot Integration Issue Log (문제 해결 로그)

본 문서는 `StudyLink` 챗봇 통합 과정에서 발생한 주요 기술적 문제들과 그 해결책을 기록합니다. 향후 유사한 문제 발생 시 참고 자료로 활용할 수 있습니다.

---

## 🛑 Issue 1: Git Push Protection (Secret Scanning) Error

### 🚨 증상 (Symptom)

- GitHub로 Push를 시도했을 때 아래와 같은 에러 메시지와 함께 거부됨.
  ```
  remote: error: GH013: Repository rule violations found for refs/heads/main.
  remote: Review all 1 secret(s) detected...
  remote: config/config.json: Google API Key detected...
  ```

### 🔍 원인 (Cause)

- `.env` 파일이나 설정 파일에 `GOOGLE_API_KEY`와 같은 민감한 정보가 포함된 채로 커밋을 시도함.
- GitHub의 보안 기능(Secret Scanning)이 이를 감지하고 차단함.

### ✅ 해결 (Solution)

1.  **파일 삭제**: 문제가 된 파일(`doc/githyp_huggingface_token.md` 등)을 로컬에서 삭제.
2.  **GitIgnore**: `.gitignore` 파일에 `.env` 및 민감한 파일 경로 추가.
3.  **히스토리 정화**: 이미 커밋된 기록을 지우기 위해 `git commit --amend` 또는 `git filter-repo` 사용 (본 프로젝트에서는 저장소 초기화 방식을 사용).

---

## 🛑 Issue 2: Hugging Face LFS (Large File) Error

### 🚨 증상 (Symptom)

- Hugging Face로 Push 할 때 10MB 이상의 파일이 거부됨.
  ```
  remote: error: File db/data_level0.bin is 64.00 MB; this exceeds GitHub's file size limit of 100.00 MB
  remote: Please use https://git-lfs.github.com/
  ```

### 🔍 원인 (Cause)

- ChromaDB의 데이터 파일(`db/*.bin`)과 엑셀 파일(`data/*.xlsx`)이 일반 Git 객체로 커밋됨.
- Hugging Face 무료 등급은 일반 파일로 10MB 이상을 허용하지 않음 (LFS 필수).

### ✅ 해결 (Solution)

1.  **Git LFS 설치**: `git lfs install` 실행.
2.  **트래킹 설정**:
    ```bash
    git lfs track "db/**"
    git lfs track "*.xlsx"
    git lfs track "data/**"
    ```
3.  **저장소 초기화 (Re-init)**: 기존 Git 히스토리에 남은 대용량 파일 흔적을 완전히 지우기 위해 `.git` 폴더를 삭제하고 `git init`으로 초기화 후 재커밋.
4.  **Force Push**: `git push origin main --force`로 깨끗한 LFS 히스토리 전송.

---

## 🛑 Issue 3: Docker Build Fail (COPY .env)

### 🚨 증상 (Symptom)

- Hugging Face 빌드 로그에서 에러 발생:
  ```
  COPY .env .
  ERROR: failed to calculate checksum... "/.env": not found
  ```

### 🔍 원인 (Cause)

- `Dockerfile` 안에 `COPY .env .` 명령어가 포함되어 있음.
- `.env` 파일은 `.gitignore`에 의해 제외되었으므로, GitHub과 Hugging Face 서버에는 존재하지 않음.

### ✅ 해결 (Solution)

1.  **Dockerfile 수정**: `COPY .env .` 라인 삭제.
2.  **Secrets 사용**: 대신 Hugging Face Space 설정(Settings) -> **Secrets** 메뉴에 `GOOGLE_API_KEY`를 환경 변수로 직접 등록.

---

## 🛑 Issue 4: Application 404 Error

### 🚨 증상 (Symptom)

- Spring Boot에서 챗봇 요청 시 `404 Not Found` 에러 발생.
- Hugging Face의 기본 404 페이지가 응답으로 옴.
  ```
  404 Not Found on POST request for "https://yaimbot23-chatbot-docker.hf.space/chat"
  ```

### 🔍 원인 (Cause)

- **닉네임 오타**: GitHub 닉네임(`yaimnot23`)과 Hugging Face 닉네임(`yaimbot23`)의 불일치로 인한 URL 주소 오류.
- **Visibility 설정**: Space가 `Private`으로 설정되어 있어 외부 접근 차단됨.

### ✅ 해결 (Solution)

1.  **URL 수정**: `ChatbotService.java`의 `AI_SERVER_URL`을 실제 닉네임(`yaimnot23`)에 맞게 수정.
2.  **Public 전환**: Hugging Face Space Settings에서 Visibility를 **Public**으로 변경.
