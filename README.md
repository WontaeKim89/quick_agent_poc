# Quick Agent POC

Azure OpenAI 기반 채팅 에이전트 POC 프로젝트

## 프로젝트 구조

```
quick_agent_poc/
├── api/                      # Backend API (FastAPI)
│   ├── main.py              # FastAPI 애플리케이션
│   ├── routers/
│   │   └── chat.py          # 채팅 API 엔드포인트 (SSE 스트리밍)
│   └── core/
│       ├── logger.py        # 로깅 유틸리티
│       └── singleton.py     # 싱글톤 패턴
├── agent/                   # LLM 관련 로직
│   └── llm_endpoint.py      # Azure OpenAI 래퍼
├── config/                  # 설정 관리
│   └── settings.py          # 환경별 설정 관리자
├── frontend/                # Frontend (Next.js)
│   ├── app/
│   │   └── api/chat/
│   │       └── route.ts     # Backend API 프록시
│   └── ...
├── start.sh                 # 통합 실행 스크립트
├── pyproject.toml           # Python 의존성 (uv)
└── .env                     # 환경변수 (gitignore)
```

## 주요 기능

- **Azure OpenAI 통합**: GPT-4o 모델 기반 채팅
- **SSE 스트리밍**: 실시간 응답 스트리밍
- **에러 처리**: SafeLLMWrapper를 통한 안전한 에러 핸들링
- **환경별 설정**: local/development/production 환경 지원
- **Key Vault 연동**: Azure Key Vault를 통한 비밀 관리

## 기술 스택

### Backend
- **Framework**: FastAPI 0.115+
- **ASGI Server**: uvicorn
- **LLM**: LangChain + Azure OpenAI
- **Python**: 3.13+
- **Package Manager**: uv

### Frontend
- **Framework**: Next.js 15
- **UI**: Assistant UI + Radix UI
- **Runtime**: React 19

## 설치 및 실행

### 1. 사전 요구사항

- Python 3.13+
- Node.js 18+
- uv (Python 패키지 매니저)
- Azure OpenAI API 키

### 2. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일을 열어 필수 환경변수 설정
# - APP_ENV=local
# - agent-azure-openai-api-key=your-api-key
# - agent-azure-openai-endpoint=your-endpoint
# - agent-azure-openai-api-version=2024-08-01-preview
```

### 3. 의존성 설치

#### Backend
```bash
# uv를 사용하여 Python 의존성 설치
uv sync
```

#### Frontend
```bash
cd frontend
npm install
cd ..
```

### 4. 서버 실행

#### 방법 1: 통합 실행 (권장)
```bash
# Frontend + Backend 동시 실행
./start.sh
```

#### 방법 2: 개별 실행

**Backend**
```bash
source .venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend**
```bash
cd frontend
npm run dev
```

### 5. 접속

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **헬스체크**: http://localhost:8000/health

## API 문서

### POST /api/chat

채팅 메시지를 전송하고 SSE 스트리밍 응답을 받습니다.

**Request Body**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "안녕하세요"
    }
  ]
}
```

**Response**
- Content-Type: `text/event-stream`
- SSE 형식의 스트리밍 응답

```
data: {"type": "text-delta", "textDelta": "안녕"}
data: {"type": "text-delta", "textDelta": "하세요!"}
data: {"type": "finish", "finishReason": "stop"}
```

## 환경변수

### 필수 환경변수

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `APP_ENV` | 환경 설정 | `local`, `development`, `production` |
| `agent-azure-openai-api-key` | Azure OpenAI API 키 | `your-api-key` |
| `agent-azure-openai-endpoint` | Azure OpenAI 엔드포인트 | `https://your-resource.openai.azure.com/` |
| `agent-azure-openai-api-version` | API 버전 | `2024-08-01-preview` |

### 선택 환경변수

- `agent-azure-search-*`: Azure Cognitive Search 관련 설정
- `agent-cosmos-*`: Cosmos DB 관련 설정
- `agent-phoenix-*`: Phoenix 관련 설정
- `agent-application-insights-connection-string`: Application Insights 연결 문자열

자세한 내용은 [.env.example](.env.example) 참고

## 개발 가이드

### 로그 확인

```bash
# Backend 로그
tail -f logs/backend.log

# Frontend 로그
tail -f logs/frontend.log
```

### 코드 구조

#### Backend API 추가하기

1. `api/routers/` 디렉토리에 새 라우터 파일 생성
2. `api/main.py`에 라우터 등록

```python
# api/routers/new_router.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/example")
async def example():
    return {"message": "example"}

# api/main.py
from api.routers import new_router
app.include_router(new_router.router, prefix="/api", tags=["new"])
```

#### LLM 모델 변경

`api/routers/chat.py`에서 모델명 변경:

```python
# 기본값: gpt-4o
llm = get_safe_llm(model_name="gpt-4o")

# 다른 모델 사용
llm = get_safe_llm(model_name="gpt-4o-mini")
```

### 환경별 설정

`config/settings.py`의 `ConfigManager`가 환경별 설정을 관리합니다:

- **local**: `.env` 파일에서 로드
- **development/production**: Azure Key Vault에서 로드 (Container Apps 환경변수 참조)

## 배포

### Azure Container App 배포 준비

1. **Dockerfile 생성** (향후 작업)
2. **Azure Container Registry에 이미지 푸시**
3. **Container App 생성 및 Key Vault 연동**

자세한 배포 가이드는 추후 추가 예정

## 트러블슈팅

### Backend 서버가 시작되지 않는 경우

```bash
# 의존성 재설치
uv sync

# 환경변수 확인
cat .env

# 로그 확인
tail -f logs/backend.log
```

### Frontend에서 Backend 연결 실패

1. Backend 서버가 실행 중인지 확인: http://localhost:8000/health
2. CORS 설정 확인: `api/main.py`의 `allow_origins`
3. Frontend의 API URL 확인: `frontend/app/api/chat/route.ts`

### Azure OpenAI API 오류

```bash
# API 키 확인
echo $agent-azure-openai-api-key

# 엔드포인트 확인
echo $agent-azure-openai-endpoint

# 로그에서 상세 오류 확인
tail -f logs/backend.log
```

## 라이선스

MIT

## 기여

이슈 및 PR은 언제든지 환영합니다!
