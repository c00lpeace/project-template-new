# 개발 가이드

## 🚀 시작하기

### 1. 환경 설정

#### 필수 도구
- Python 3.12+
- PostgreSQL 14+
- Redis 7+
- Git

#### 저장소 클론
```bash
git clone <repository-url>
cd project-template-new/ai_backend
```

#### 가상환경 생성
```bash
python -m venv venv_py312
source venv_py312/bin/activate  # Windows: venv_py312\Scripts\activate
```

#### 의존성 설치
```bash
pip install -r requirements.txt
```

---

### 2. 환경 변수 설정

`.env` 파일 생성:
```bash
# Database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=plc_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
CACHE_ENABLED=true

# AWS S3
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_S3_BUCKET=your-bucket
AWS_REGION=ap-northeast-2

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Application
APP_DEBUG=true
APP_LOG_LEVEL=debug
LOG_TO_FILE=true
```

---

### 3. 데이터베이스 초기화

```bash
# PostgreSQL 데이터베이스 생성
createdb plc_db

# 테이블 자동 생성 (앱 시작 시 자동 실행됨)
python -m uvicorn src.main:app --reload
```

---

### 4. 로컬 실행

```bash
cd D:\project-template-new\ai_backend
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

접속:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📁 프로젝트 구조 설명

```
ai_backend/
├── src/
│   ├── api/              # API Layer
│   │   ├── routers/     # 라우터 (컨트롤러)
│   │   └── services/    # 비즈니스 로직
│   ├── database/        # Database Layer
│   │   ├── models/     # SQLAlchemy 모델
│   │   └── crud/       # CRUD 작업
│   ├── types/           # Type Definitions
│   │   ├── request/    # 요청 스키마 (Pydantic)
│   │   └── response/   # 응답 스키마 (Pydantic)
│   ├── core/            # Core Utilities
│   ├── config/          # 설정
│   └── main.py          # 애플리케이션 진입점
```

---

## 🏗️ 개발 규칙

### 1. 파일 네이밍
- 모델: `{entity}_models.py` (예: `user_models.py`)
- CRUD: `{entity}_crud.py` (예: `user_crud.py`)
- 서비스: `{entity}_service.py` (예: `user_service.py`)
- 라우터: `{entity}_router.py` (예: `user_router.py`)

### 2. 코드 스타일
```python
# 임포트 순서
# 1. 표준 라이브러리
import logging
from typing import List, Optional

# 2. 서드파티 라이브러리
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# 3. 로컬 모듈
from src.core.dependencies import get_db
from src.database.models.user_models import User
```

### 3. 로깅
```python
import logging

logger = logging.getLogger(__name__)

def some_function():
    logger.info("정보 로그")
    logger.debug("디버그 로그")
    logger.warning("경고 로그")
    logger.error("에러 로그")
```

---

## 🔨 새 기능 추가 가이드

### 1. 새 엔티티 추가

#### Step 1: 모델 생성
```python
# src/database/models/example_models.py
from sqlalchemy import Column, String, Boolean
from src.database.base import Base

class Example(Base):
    __tablename__ = "EXAMPLES"
    
    example_id = Column("EXAMPLE_ID", String(50), primary_key=True)
    name = Column("NAME", String(100), nullable=False)
    is_active = Column("IS_ACTIVE", Boolean, default=True)
```

#### Step 2: CRUD 생성
```python
# src/database/crud/example_crud.py
from sqlalchemy.orm import Session
from src.database.models.example_models import Example

class ExampleCRUD:
    def __init__(self, db: Session):
        self.db = db
    
    def get_example(self, example_id: str) -> Example:
        return self.db.query(Example).filter(
            Example.example_id == example_id
        ).first()
    
    def create_example(self, example_id: str, name: str) -> Example:
        example = Example(example_id=example_id, name=name)
        self.db.add(example)
        self.db.commit()
        self.db.refresh(example)
        return example
```

#### Step 3: 요청/응답 스키마 생성
```python
# src/types/request/example_request.py
from pydantic import BaseModel

class CreateExampleRequest(BaseModel):
    example_id: str
    name: str

# src/types/response/example_response.py
from pydantic import BaseModel

class ExampleResponse(BaseModel):
    example_id: str
    name: str
    is_active: bool
    
    class Config:
        from_attributes = True
```

#### Step 4: 서비스 생성
```python
# src/api/services/example_service.py
from sqlalchemy.orm import Session
from src.database.crud.example_crud import ExampleCRUD
from src.types.response.exceptions import HandledException

class ExampleService:
    def __init__(self, db: Session):
        self.crud = ExampleCRUD(db)
    
    def get_example(self, example_id: str):
        example = self.crud.get_example(example_id)
        if not example:
            raise HandledException(
                code="EXAMPLE_NOT_FOUND",
                message="예제를 찾을 수 없습니다"
            )
        return example
```

#### Step 5: 라우터 생성
```python
# src/api/routers/example_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.core.dependencies import get_db
from src.api.services.example_service import ExampleService
from src.types.request.example_request import CreateExampleRequest
from src.types.response.example_response import ExampleResponse

router = APIRouter(prefix="/examples", tags=["example"])

@router.get("/{example_id}", response_model=ExampleResponse)
def get_example(
    example_id: str,
    db: Session = Depends(get_db)
):
    service = ExampleService(db)
    example = service.get_example(example_id)
    return ExampleResponse.from_orm(example)
```

#### Step 6: 라우터 등록
```python
# src/main.py
from src.api.routers.example_router import router as example_router

app.include_router(example_router, prefix="/v1")
```

---

## 🧪 테스트

### 단위 테스트
```python
import pytest
from src.database.crud.example_crud import ExampleCRUD

def test_create_example(db_session):
    crud = ExampleCRUD(db_session)
    example = crud.create_example("test_001", "Test Example")
    
    assert example.example_id == "test_001"
    assert example.name == "Test Example"
```

### API 테스트
```python
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_get_example():
    response = client.get("/v1/examples/test_001")
    assert response.status_code == 200
    assert response.json()["example_id"] == "test_001"
```

---

## 🔍 디버깅

### VSCode 디버그 설정
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "src.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true
    }
  ]
}
```

### 로그 레벨 조정
```bash
# .env 파일
APP_LOG_LEVEL=debug      # debug, info, warning, error
SERVER_LOG_LEVEL=info
```

---

## 📝 커밋 메시지 규칙

```
feat: 새 기능 추가
fix: 버그 수정
docs: 문서 변경
style: 코드 포맷팅
refactor: 리팩토링
test: 테스트 추가/수정
chore: 기타 변경사항
```

예시:
```
feat: 사용자 검색 API 추가
fix: 프로그램 목록 조회 시 권한 필터링 오류 수정
docs: API 문서 업데이트
```

---

## 🐛 트러블슈팅

### 데이터베이스 연결 오류
```bash
# PostgreSQL 서비스 확인
sudo systemctl status postgresql

# 연결 테스트
psql -h localhost -U postgres -d plc_db
```

### Redis 연결 오류
```bash
# Redis 서비스 확인
redis-cli ping
# 응답: PONG
```

### 임포트 에러
```bash
# PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:${PWD}"
```

---

**작성일**: 2025-01-17  
**최종 수정일**: 2025-01-17
