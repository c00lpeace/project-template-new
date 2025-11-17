# 데이터베이스 스키마 문서

## 📊 ERD 개요

이 문서는 프로젝트의 모든 데이터베이스 테이블과 관계를 정의합니다.

## 🗂️ 테이블 분류

### 1. 사용자 및 권한 관리
- `USERS`: 사용자 정보
- `PERMISSION_GROUPS`: 권한 그룹
- `USER_GROUP_MAPPINGS`: 사용자-그룹 매핑
- `GROUP_PROCESS_PERMISSIONS`: 그룹별 공정 권한

### 2. 프로그램 관리
- `PROGRAMS`: 프로그램 마스터
- `PROCESSING_FAILURES`: 처리 실패 정보
- `PROGRAM_LLM_DATA_CHUNKS`: LLM 데이터 청크

### 3. 문서 관리
- `DOCUMENTS`: 문서 메타데이터
- `DOCUMENT_CHUNKS`: 문서 청크 (임베딩)
- `PROCESSING_JOBS`: 문서 처리 작업

### 4. 기준정보 (마스터 데이터)
- `PLANT_MASTER`: 공장
- `PROCESS_MASTER`: 공정
- `LINE_MASTER`: 라인
- `EQUIPMENT_GROUP_MASTER`: 장비 그룹

### 5. PLC 관리
- `PLC`: PLC 정보 (스냅샷 포함)
- `PLC_HISTORY`: PLC 변경 이력

### 6. 채팅 관리
- `CHATS`: 채팅 세션
- `CHAT_MESSAGES`: 채팅 메시지
- `MESSAGE_RATINGS`: 메시지 평가

### 7. 템플릿 관리
- `TEMPLATES`: 템플릿 정보
- `TEMPLATE_DATA`: 템플릿 데이터

### 8. 지식 베이스
- `KNOWLEDGE_REFERENCES`: 미쯔비시 매뉴얼, 용어집 등

---

## 📋 주요 테이블 상세

### USERS (사용자)
```sql
CREATE TABLE USERS (
    USER_ID VARCHAR(50) PRIMARY KEY,
    EMPLOYEE_ID VARCHAR(20) UNIQUE NOT NULL,
    NAME VARCHAR(100) NOT NULL,
    SITE_LIST JSON,                    -- 접근 가능한 사이트 목록
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    UPDATE_DT TIMESTAMP,
    IS_ACTIVE BOOLEAN NOT NULL DEFAULT TRUE,
    IS_DELETED BOOLEAN NOT NULL DEFAULT FALSE
);
```

**컬럼 설명**:
- `USER_ID`: 사용자 고유 식별자
- `EMPLOYEE_ID`: 사번 (unique)
- `NAME`: 사용자 이름
- `SITE_LIST`: 접근 가능한 사이트 목록 (JSON 배열)
- `IS_ACTIVE`: 활성화 상태
- `IS_DELETED`: 소프트 삭제 여부

**인덱스**:
```sql
CREATE INDEX idx_users_employee_id ON USERS(EMPLOYEE_ID);
CREATE INDEX idx_users_active ON USERS(IS_ACTIVE);
```

---

### PROGRAMS (프로그램)
```sql
CREATE TABLE PROGRAMS (
    PROGRAM_ID VARCHAR(50) PRIMARY KEY,
    PROGRAM_NAME VARCHAR(255) NOT NULL,
    DESCRIPTION TEXT,
    PROCESS_ID VARCHAR(50) REFERENCES PROCESS_MASTER(PROCESS_ID),
    STATUS VARCHAR(50) NOT NULL DEFAULT 'preparing',
    ERROR_MESSAGE TEXT,
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50) NOT NULL,
    UPDATE_DT TIMESTAMP,
    UPDATE_USER VARCHAR(50),
    COMPLETED_AT TIMESTAMP,
    IS_USED BOOLEAN NOT NULL DEFAULT TRUE,
    IS_DELETED BOOLEAN NOT NULL DEFAULT FALSE,
    DELETED_AT TIMESTAMP,
    DELETED_BY VARCHAR(50)
);
```

**상태 값**:
- `preparing`: 준비 중
- `uploading`: 업로드 중
- `processing`: 처리 중
- `embedding`: 임베딩 중
- `completed`: 완료
- `failed`: 실패
- `indexing_failed`: 인덱싱 실패

**인덱스**:
```sql
CREATE INDEX idx_programs_process_id ON PROGRAMS(PROCESS_ID);
CREATE INDEX idx_programs_status ON PROGRAMS(STATUS);
CREATE INDEX idx_programs_is_deleted ON PROGRAMS(IS_DELETED);
```

---

### DOCUMENTS (문서)
```sql
CREATE TABLE DOCUMENTS (
    DOCUMENT_ID VARCHAR(50) PRIMARY KEY,
    DOCUMENT_NAME VARCHAR(255) NOT NULL,
    ORIGINAL_FILENAME VARCHAR(255) NOT NULL,
    FILE_KEY VARCHAR(500),                -- S3 Key
    FILE_SIZE INTEGER,
    FILE_TYPE VARCHAR(100),               -- MIME Type
    FILE_EXTENSION VARCHAR(20),
    UPLOAD_PATH VARCHAR(500),
    FILE_HASH VARCHAR(255),
    USER_ID VARCHAR(50),
    IS_PUBLIC BOOLEAN DEFAULT FALSE,
    DOCUMENT_TYPE VARCHAR(50),
    STATUS VARCHAR(50) NOT NULL DEFAULT 'pending',
    TOTAL_PAGES INTEGER,
    PROCESSED_PAGES INTEGER,
    ERROR_MESSAGE TEXT,
    MILVUS_COLLECTION_NAME VARCHAR(255),
    VECTOR_COUNT INTEGER,
    LANGUAGE VARCHAR(10),
    AUTHOR VARCHAR(255),
    SUBJECT VARCHAR(255),
    METADATA_JSON JSON,
    PROCESSING_CONFIG JSON,
    PERMISSIONS JSON,
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    UPDATED_AT TIMESTAMP,
    PROCESSED_AT TIMESTAMP,
    IS_DELETED BOOLEAN NOT NULL DEFAULT FALSE,
    PROGRAM_ID VARCHAR(50) REFERENCES PROGRAMS(PROGRAM_ID),
    PROGRAM_FILE_TYPE VARCHAR(50),        -- ladder_logic, comment, template, processed_json
    SOURCE_DOCUMENT_ID VARCHAR(50) REFERENCES DOCUMENTS(DOCUMENT_ID),
    KNOWLEDGE_REFERENCE_ID VARCHAR(50) REFERENCES KNOWLEDGE_REFERENCES(REFERENCE_ID)
);
```

**문서 타입** (`PROGRAM_FILE_TYPE`):
- `ladder_logic`: 래더 로직 파일 (ZIP)
- `comment`: 코멘트 파일 (CSV)
- `template`: 템플릿 파일 (XLSX)
- `processed_json`: 전처리된 JSON 파일

**인덱스**:
```sql
CREATE INDEX idx_documents_program_id ON DOCUMENTS(PROGRAM_ID);
CREATE INDEX idx_documents_status ON DOCUMENTS(STATUS);
CREATE INDEX idx_documents_user_id ON DOCUMENTS(USER_ID);
```

---

### PLC (PLC 정보)
```sql
CREATE TABLE PLC (
    ID VARCHAR(50) PRIMARY KEY,
    PLC_ID VARCHAR(50),
    PLC_NAME VARCHAR(255),
    UNIT VARCHAR(50),
    PROGRAM_ID VARCHAR(50) UNIQUE REFERENCES PROGRAMS(PROGRAM_ID),
    MAPPING_DT TIMESTAMP,
    MAPPING_USER VARCHAR(50),
    IS_ACTIVE BOOLEAN NOT NULL DEFAULT TRUE,
    METADATA_JSON JSON,
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50) NOT NULL,
    UPDATE_DT TIMESTAMP,
    UPDATE_USER VARCHAR(50),
    
    -- 스냅샷 (PLC 생성/수정 시점의 기준정보)
    PLANT_ID_SNAPSHOT VARCHAR(50),
    PLANT_CODE_SNAPSHOT VARCHAR(50),
    PLANT_NAME_SNAPSHOT VARCHAR(255),
    PROCESS_ID_SNAPSHOT VARCHAR(50),
    PROCESS_CODE_SNAPSHOT VARCHAR(50),
    PROCESS_NAME_SNAPSHOT VARCHAR(255),
    LINE_ID_SNAPSHOT VARCHAR(50),
    LINE_CODE_SNAPSHOT VARCHAR(50),
    LINE_NAME_SNAPSHOT VARCHAR(255),
    EQUIPMENT_GROUP_ID_SNAPSHOT VARCHAR(50),
    EQUIPMENT_GROUP_CODE_SNAPSHOT VARCHAR(50),
    EQUIPMENT_GROUP_NAME_SNAPSHOT VARCHAR(255),
    
    -- 현재 기준정보 참조
    PLANT_ID_CURRENT VARCHAR(50) REFERENCES PLANT_MASTER(PLANT_ID),
    PROCESS_ID_CURRENT VARCHAR(50) REFERENCES PROCESS_MASTER(PROCESS_ID),
    LINE_ID_CURRENT VARCHAR(50) REFERENCES LINE_MASTER(LINE_ID),
    EQUIPMENT_GROUP_ID_CURRENT VARCHAR(50) REFERENCES EQUIPMENT_GROUP_MASTER(EQUIPMENT_GROUP_ID)
);
```

**설계 특징**:
- **스냅샷**: PLC 생성 시점의 계층 구조 저장 (불변)
- **현재 참조**: 현재 기준정보 참조 (변경 가능)
- **1:1 관계**: 1개 PLC → 1개 Program (PROGRAM_ID UNIQUE)

**인덱스**:
```sql
CREATE INDEX idx_plc_program_id ON PLC(PROGRAM_ID);
CREATE INDEX idx_plc_process_current ON PLC(PROCESS_ID_CURRENT);
```

---

### CHAT_MESSAGES (채팅 메시지)
```sql
CREATE TABLE CHAT_MESSAGES (
    MESSAGE_ID VARCHAR(50) PRIMARY KEY,
    CHAT_ID VARCHAR(50) NOT NULL REFERENCES CHATS(CHAT_ID),
    USER_ID VARCHAR(50),
    MESSAGE TEXT NOT NULL,
    MESSAGE_TYPE VARCHAR(20) NOT NULL,
    STATUS VARCHAR(20) NOT NULL DEFAULT 'completed',
    TIMESTAMP TIMESTAMP NOT NULL DEFAULT NOW(),
    IS_DELETED BOOLEAN NOT NULL DEFAULT FALSE,
    METADATA_JSON JSON,
    
    -- PLC 계층 스냅샷 (채팅 시점의 PLC 정보)
    PLC_HIERARCHY_SNAPSHOT JSON
);
```

**PLC 계층 스냅샷 예시**:
```json
{
  "plc_uuid": "plc_001",
  "plc_id": "PLC-01",
  "plc_name": "메인 PLC",
  "unit": "1호기",
  "plant_code": "P001",
  "plant_name": "BOSK KY",
  "process_code": "PRC-001",
  "process_name": "전극 공정",
  "line_code": "L001",
  "line_name": "Line 1",
  "equipment_group_code": "EQ-001",
  "equipment_group_name": "장비 그룹 1"
}
```

---

### PERMISSION_GROUPS (권한 그룹)
```sql
CREATE TABLE PERMISSION_GROUPS (
    GROUP_ID VARCHAR(50) PRIMARY KEY,
    GROUP_NAME VARCHAR(255) NOT NULL,
    DESCRIPTION TEXT,
    IS_ACTIVE BOOLEAN NOT NULL DEFAULT TRUE,
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50),
    UPDATE_DT TIMESTAMP,
    UPDATE_USER VARCHAR(50)
);
```

---

### GROUP_PROCESS_PERMISSIONS (그룹별 공정 권한)
```sql
CREATE TABLE GROUP_PROCESS_PERMISSIONS (
    PERMISSION_ID VARCHAR(50) PRIMARY KEY,
    GROUP_ID VARCHAR(50) NOT NULL REFERENCES PERMISSION_GROUPS(GROUP_ID),
    PROCESS_ID VARCHAR(50) NOT NULL REFERENCES PROCESS_MASTER(PROCESS_ID),
    ACCESS_LEVEL VARCHAR(20) NOT NULL DEFAULT 'read',
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50)
);
```

**접근 레벨**:
- `read`: 읽기
- `write`: 읽기 + 쓰기
- `admin`: 모든 권한

---

### PROCESSING_FAILURES (처리 실패)
```sql
CREATE TABLE PROCESSING_FAILURES (
    FAILURE_ID VARCHAR(50) PRIMARY KEY,
    SOURCE_TYPE VARCHAR(50) NOT NULL,     -- 'program', 'knowledge_reference'
    SOURCE_ID VARCHAR(50) NOT NULL,
    FAILURE_TYPE VARCHAR(50) NOT NULL,
    FILE_PATH VARCHAR(500),
    FILE_INDEX INTEGER,
    FILENAME VARCHAR(255),
    S3_PATH VARCHAR(500),
    S3_KEY VARCHAR(500),
    ERROR_MESSAGE TEXT NOT NULL,
    ERROR_DETAILS JSON,
    RETRY_COUNT INTEGER NOT NULL DEFAULT 0,
    MAX_RETRY_COUNT INTEGER NOT NULL DEFAULT 3,
    STATUS VARCHAR(50) NOT NULL DEFAULT 'pending',
    RESOLVED_AT TIMESTAMP,
    LAST_RETRY_AT TIMESTAMP,
    RESOLVED_BY VARCHAR(50),
    METADATA_JSON JSON,
    CREATED_AT TIMESTAMP NOT NULL DEFAULT NOW(),
    UPDATED_AT TIMESTAMP
);
```

**실패 타입**:
- `preprocessing`: 전처리 실패
- `document_storage`: 문서 저장 실패
- `vector_indexing`: 벡터 인덱싱 실패

**상태**:
- `pending`: 대기 중
- `retrying`: 재시도 중
- `resolved`: 해결됨
- `failed`: 실패 (재시도 불가)

---

## 🔗 관계 설명

### 1. 프로그램 - 문서
```
PROGRAMS (1) ─────< (N) DOCUMENTS
```
- 1개 프로그램은 여러 문서를 가질 수 있음
- 문서 타입: 래더 로직, 코멘트, 템플릿, 전처리 JSON

### 2. PLC - 프로그램
```
PLC (1) ───── (1) PROGRAMS
```
- 1개 PLC는 1개 프로그램만 매핑 가능 (UNIQUE 제약)

### 3. 사용자 - 그룹 - 공정
```
USERS (N) ────< USER_GROUP_MAPPINGS >──── (N) PERMISSION_GROUPS
                                                    │
                                                    └< GROUP_PROCESS_PERMISSIONS >─ (N) PROCESS_MASTER
```
- 다대다 관계: 사용자는 여러 그룹에 속할 수 있음
- 그룹은 여러 공정에 권한을 가질 수 있음

### 4. 기준정보 계층
```
PLANT_MASTER (1) ────< (N) PROCESS_MASTER
PROCESS_MASTER (1) ───< (N) LINE_MASTER
LINE_MASTER (1) ──────< (N) EQUIPMENT_GROUP_MASTER
```

### 5. 채팅 - 메시지
```
CHATS (1) ─────< (N) CHAT_MESSAGES
```

---

## 🔍 주요 쿼리 패턴

### 사용자가 접근 가능한 공정 조회
```sql
SELECT DISTINCT pm.PROCESS_ID, pm.PROCESS_NAME
FROM PROCESS_MASTER pm
JOIN GROUP_PROCESS_PERMISSIONS gpp ON pm.PROCESS_ID = gpp.PROCESS_ID
JOIN USER_GROUP_MAPPINGS ugm ON gpp.GROUP_ID = ugm.GROUP_ID
WHERE ugm.USER_ID = :user_id
  AND pm.IS_ACTIVE = TRUE
  AND gpp.ACCESS_LEVEL IN ('read', 'write', 'admin');
```

### 프로그램 목록 조회 (권한 필터링)
```sql
SELECT p.*
FROM PROGRAMS p
WHERE p.IS_DELETED = FALSE
  AND (p.PROCESS_ID IS NULL 
       OR p.PROCESS_ID IN (
           SELECT DISTINCT gpp.PROCESS_ID
           FROM GROUP_PROCESS_PERMISSIONS gpp
           JOIN USER_GROUP_MAPPINGS ugm ON gpp.GROUP_ID = ugm.GROUP_ID
           WHERE ugm.USER_ID = :user_id
       ))
ORDER BY p.CREATE_DT DESC;
```

### PLC 계층 정보 조회 (스냅샷)
```sql
SELECT 
    PLC_ID,
    PLC_NAME,
    UNIT,
    PLANT_CODE_SNAPSHOT || ' > ' || 
    PROCESS_CODE_SNAPSHOT || ' > ' || 
    LINE_CODE_SNAPSHOT || ' > ' || 
    EQUIPMENT_GROUP_CODE_SNAPSHOT AS HIERARCHY_PATH,
    PLANT_NAME_SNAPSHOT,
    PROCESS_NAME_SNAPSHOT,
    LINE_NAME_SNAPSHOT,
    EQUIPMENT_GROUP_NAME_SNAPSHOT
FROM PLC
WHERE ID = :plc_uuid;
```

---

## 📝 참고사항

### 소프트 삭제
대부분의 테이블은 `IS_DELETED` 플래그를 사용한 소프트 삭제를 지원합니다.

### 타임스탬프
- `CREATE_DT`: 생성 일시
- `UPDATE_DT`: 수정 일시
- `DELETED_AT`: 삭제 일시

### JSON 필드
- `METADATA_JSON`: 확장 가능한 메타데이터
- `PERMISSIONS`: 문서별 권한 설정
- `PROCESSING_CONFIG`: 문서 처리 설정

---

**작성일**: 2025-01-17  
**최종 수정일**: 2025-01-17  
**참조 문서**: 
- `ai_backend/COMPLETE_ERD.md`
- `ai_backend/REVISED_TABLE_SCHEMA.md`
