# 프로젝트 개요

## 📌 프로젝트 정보

### 기본 정보
- **프로젝트명**: PLC Interpreter Application Backend
- **프레임워크**: FastAPI
- **ORM**: SQLAlchemy
- **데이터베이스**: PostgreSQL
- **Python 버전**: 3.12+
- **캐시**: Redis
- **벡터 DB**: Milvus
- **파일 저장소**: AWS S3

### 프로젝트 디렉토리 구조
```
D:\project-template-new/
├── ai_backend/              # FastAPI 백엔드 애플리케이션
│   ├── src/                 # 소스 코드
│   │   ├── api/            # API 엔드포인트
│   │   │   ├── routers/   # 라우터 (컨트롤러)
│   │   │   └── services/  # 비즈니스 로직
│   │   ├── cache/          # 캐시 관련
│   │   ├── config/         # 설정 파일
│   │   ├── core/           # 핵심 기능 (의존성, 예외 처리 등)
│   │   ├── database/       # 데이터베이스 관련
│   │   │   ├── models/    # SQLAlchemy 모델
│   │   │   └── crud/      # CRUD 작업
│   │   ├── middleware/     # 미들웨어
│   │   ├── types/          # 타입 정의
│   │   │   ├── request/   # 요청 스키마
│   │   │   └── response/  # 응답 스키마
│   │   ├── utils/          # 유틸리티
│   │   └── main.py         # 애플리케이션 진입점
│   ├── logs/               # 로그 파일
│   ├── uploads/            # 업로드 파일 임시 저장
│   ├── .env                # 환경 변수
│   ├── requirements.txt    # Python 의존성
│   └── Dockerfile          # Docker 이미지
├── doc_processor/          # 문서 처리 파이프라인 (Prefect)
├── shared_core/            # 공통 모듈
├── k8s-infra/             # Kubernetes 설정
└── docs/                   # 프로젝트 문서 (이 폴더)
```

## 🎯 주요 기능

### 1. 사용자 관리
- 사용자 CRUD
- 권한 그룹 기반 관리
- 사용자별 사이트 접근 제어

### 2. 프로그램 관리 (PLC Program)
- 프로그램 등록 (ZIP, XLSX, CSV 업로드)
- 파일 전처리 및 S3 업로드
- 프로그램 검색 및 목록 조회
- 처리 진행률 추적
- 실패 파일 재시도

### 3. PLC 관리
- PLC 계층 구조 관리 (Plant → Process → Line → PLC → 호기)
- PLC-Program 매핑
- 스냅샷 기반 버전 관리

### 4. 문서 관리
- 문서 업로드/다운로드
- 문서 임베딩 및 벡터화
- 문서 검색 (키워드 + 벡터)
- 권한 기반 접근 제어

### 5. AI 채팅
- LLM 기반 대화형 인터페이스
- 스트리밍 응답 지원
- 채팅 히스토리 관리
- 메시지 평가 기능
- PLC 컨텍스트 기반 답변

### 6. 기준정보 관리
- Plant/Process/Line/PLC 마스터
- 미쯔비시 기준정보
- 용어집 관리

## 🏗️ 아키텍처 패턴

### Layered Architecture
```
┌─────────────────────────────────────┐
│     Presentation Layer (Router)     │
│  - API 엔드포인트                    │
│  - 요청/응답 검증                    │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│    Business Logic Layer (Service)   │
│  - 비즈니스 로직                     │
│  - 트랜잭션 관리                     │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│   Data Access Layer (CRUD/Model)    │
│  - DB 작업                          │
│  - 쿼리 실행                        │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│          Database (PostgreSQL)       │
└─────────────────────────────────────┘
```

### 핵심 설계 원칙
1. **관심사의 분리 (Separation of Concerns)**
   - Router: HTTP 요청/응답만 처리
   - Service: 비즈니스 로직만 처리
   - CRUD: DB 작업만 처리

2. **의존성 주입 (Dependency Injection)**
   - FastAPI Depends를 통한 의존성 관리
   - 테스트 용이성 확보

3. **타입 안전성 (Type Safety)**
   - Pydantic을 통한 요청/응답 검증
   - SQLAlchemy 모델을 통한 DB 타입 보장

4. **예외 처리 (Exception Handling)**
   - 계층별 예외 처리
   - 글로벌 예외 핸들러를 통한 일관된 에러 응답

## 🔌 외부 시스템 연동

### AWS S3
- 프로그램 파일 저장
- 문서 파일 저장
- 이미지 파일 저장

### Redis
- 채팅 히스토리 캐싱
- 드롭다운 데이터 캐싱
- 세션 관리

### Milvus
- 문서 벡터 저장
- 유사도 검색

### OpenAI API (Azure)
- LLM 채팅 (GPT-4)
- 이미지 분석 (GPT-4 Vision)
- 텍스트 임베딩

### Prefect (doc_processor)
- 문서 처리 파이프라인
- 임베딩 작업 스케줄링

## 📊 데이터 흐름

### 프로그램 등록 플로우
```
1. 사용자 파일 업로드 (ZIP/XLSX/CSV)
   ↓
2. 파일 검증 및 임시 저장
   ↓
3. S3 업로드
   ↓
4. DB 메타데이터 저장 (DOCUMENTS, PROGRAMS)
   ↓
5. 백그라운드 처리 (Prefect)
   - 파일 파싱
   - 임베딩 생성
   - Milvus 저장
   ↓
6. 처리 완료 (상태 업데이트)
```

### 채팅 플로우
```
1. 사용자 메시지 입력
   ↓
2. 메시지 저장 (Redis + DB)
   ↓
3. 컨텍스트 검색 (Milvus)
   ↓
4. LLM 호출 (OpenAI API)
   ↓
5. 스트리밍 응답 생성
   ↓
6. AI 응답 저장 (Redis + DB)
```

## 🔐 보안 및 권한

### 권한 모델
- 권한 그룹 기반 관리 (PERMISSION_GROUPS)
- 사용자-그룹 매핑 (USER_GROUP_MAPPINGS)
- 그룹-공정 권한 (GROUP_PROCESS_PERMISSIONS)

### 접근 제어
- API 레벨: 사용자 ID 기반 검증
- 데이터 레벨: Process ID 기반 필터링
- 파일 레벨: S3 Pre-signed URL

## 📝 API 버전 관리
- 현재 버전: v1
- API Prefix: `/v1`
- Root Path: 설정 가능 (APP_ROOT_PATH)

## 🚀 배포 환경
- **로컬 개발**: Docker Compose
- **개발 서버**: Kubernetes (dev namespace)
- **운영 서버**: Kubernetes (prod namespace)

---

**작성일**: 2025-01-17  
**최종 수정일**: 2025-01-17
