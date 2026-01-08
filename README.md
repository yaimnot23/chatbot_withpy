---
title: Univ Admission Chatbot
emoji: 🎓
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# University Admission AI Consultant

이 프로젝트는 대입 입시 데이터를 바탕으로 상담을 제공하는 AI 챗봇입니다.

## 배포 정보

- **SDK**: Docker
- **Port**: 7860
- **API**: FastAPI
- **Model**: Google Gemini Flash

## 로컬 실행 방법

```bash
python server.py
```

또는

```bash
docker build -t chatbot .
docker run -p 7860:7860 chatbot
```
