# API 정의서

## 📌 API 개요

### 기본 정보
- **Base URL**: `http://localhost:8000` (로컬)
- **API Prefix**: `/v1`
- **응답 형식**: JSON
- **문자 인코딩**: UTF-8
- **API 문서**: http://localhost:8000/docs

### 공통 응답 형식

#### 성공 응답
```json
{
  "user_id": "user001",
  "message": "Success"
}
```

#### 에러 응답
```json
{
  "detail": {
    "code": "USER_NOT_FOUND",
    "message": "사용자를 찾을 수 없습니다"
  }
}
```

---

## 1️⃣ 사용자 관리 API

### POST /v1/users - 사용자 생성
**Request:**
```json
{
  "user_id": "user001",
  "employee_id": "20250001",
  "name": "홍길동"
}
```

**Response (201):**
```json
{
  "user_id": "user001",
  "employee_id": "20250001",
  "name": "홍길동"
}
```

### GET /v1/users/{user_id} - 사용자 조회
**Response (200):**
```json
{
  "user_id": "user001",
  "employee_id": "20250001",
  "name": "홍길동",
  "is_active": true
}
```

### GET /v1/users - 사용자 목록 조회
**Parameters:**
- skip (int): 건너뛸 개수 (default: 0)
- limit (int): 조회할 개수 (default: 100)
- is_active (bool): 활성 상태 필터

---

## 2️⃣ 프로그램 관리 API

### POST /v1/programs/register - 프로그램 등록
**Request (multipart/form-data):**
- program_name (string)
- user_id (string)
- zip_file (file)
- comment_file (file)

**Response (201):**
```json
{
  "program_id": "PGM_000001",
  "status": "uploading"
}
```

### GET /v1/programs - 프로그램 목록 조회
**Parameters:**
- page (int): 페이지 번호
- page_size (int): 페이지당 항목 수
- status (string): 상태 필터
- keyword (string): 검색 키워드

---

## 3️⃣ PLC 관리 API

### GET /v1/plcs - PLC 목록 조회
**Parameters:**
- page (int)
- page_size (int)
- plc_id (string): PLC ID 검색
- program_name (string): 프로그램명 필터

**Response (200):**
```json
{
  "plcs": [{
    "id": "plc_uuid_001",
    "plc_id": "PLC-001",
    "plc_name": "메인 PLC",
    "program_id": "PGM_000001"
  }],
  "total_count": 1
}
```

### POST /v1/plcs/mapping - PLC-Program 매핑
**Request:**
```json
{
  "plc_uuid": "plc_uuid_001",
  "program_id": "PGM_000001",
  "user_id": "user001"
}
```

---

## 4️⃣ 채팅 API

### POST /v1/chat - 채팅 생성
**Request:**
```json
{
  "user_id": "user001",
  "chat_title": "PLC 질문"
}
```

### POST /v1/chat/{chat_id}/stream - 메시지 전송 (스트리밍)
**Request:**
```json
{
  "message": "PLC-001을 설명해주세요",
  "user_id": "user001",
  "plc_uuid": "plc_uuid_001"
}
```

**Response (SSE):**
```
data: {"type":"stream","content":"PLC"}
data: {"type":"end"}
```

### GET /v1/chat/{chat_id}/history - 채팅 히스토리 조회
**Parameters:**
- user_id (string)

---

**작성일**: 2025-01-17  
**Swagger UI**: http://localhost:8000/docs
