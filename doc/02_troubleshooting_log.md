# 02. 문제 해결 로그 (Troubleshooting Log)

개발 및 배포 과정에서 발생했던 주요 이슈와 해결 방법을 기록하여, 향후 유사한 문제 발생 시 참고할 수 있도록 합니다.

---

## 🛑 Issue 1: GitHub Secret Scanning (API Key 노출)

- **현상**: `.env`에 들어있던 Google API Key가 GitHub로 Push 되려 할 때 보안 시스템에 의해 차단됨.
- **해결**:
  1.  `.gitignore`에 `.env` 및 민감한 파일을 확실히 포함함.
  2.  노출된 기록이 있는 Git 히스토리를 정화(Rewrite)하여 보안 위험을 제거함.

## 🛑 Issue 2: Git LFS 대용량 파일 배포 오류

- **현상**: ChromaDB 데이터(`db/`)와 엑셀 파일이 10MB를 초과하여 Hugging Face로 배포되지 않음.
- **해결**:
  1.  `git lfs install`로 대용량 파일 관리 도구 설치.
  2.  `git lfs track "db/**"` 등으로 추적 설정.
  3.  LFS 히스토리를 깨끗하게 다시 만들기 위해 저장소 초기화 후 Force Push 진행.

## 🛑 Issue 3: Docker 빌드 실패 (.env 파일 미존재)

- **현상**: `Dockerfile` 내에 `COPY .env .` 명령어가 있었으나, 실제 클라우드에는 `.env`가 없어 빌드가 깨짐.
- **해결**:
  1.  `Dockerfile`에서 `COPY .env` 라인 삭제.
  2.  Hugging Face **Settings -> Secrets** 메뉴에서 `GOOGLE_API_KEY`를 직접 등록하여 보안과 빌드 안정성을 모두 확보함.

## 🛑 Issue 4: 서버 연결 404 에러 (주소 불일치)

- **현상**: Spring Boot에서 요청을 보냈으나 계속 404(Not Found) 응답을 받음.
- **원인**: GitHub 닉네임과 Hugging Face 닉네임 불일치 및 Space 이름 오타.
- **해결**: `ChatbotService.java`의 URL 주소를 실제 Hugging Face Public URL로 정확하게 수정하고, Space의 Visibility를 **Public**으로 설정함.
