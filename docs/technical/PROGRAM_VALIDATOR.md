# Program Validator 기술 문서

## 📌 개요

### 기본 정보
- **모듈명**: `program_validator.py`
- **위치**: `ai_backend/src/api/services/program_validator.py`
- **목적**: PLC 프로그램 파일 유효성 검증
- **역할**: 업로드된 프로그램 파일들(레더 ZIP, 템플릿 XLSX, 커멘트 CSV)의 형식 및 내용 검증

### 의존성
```python
# 외부 라이브러리
- pandas: XLSX/CSV 파일 처리
- zipfile: ZIP 압축 파일 처리
- fastapi.UploadFile: 업로드 파일 핸들링

# 내부 모듈
- src.config.simple_settings: 환경 설정값
```

---

## 🏗️ 클래스 구조

### `ProgramValidator` 클래스

프로그램 파일 유효성 검사를 담당하는 정적 메서드 기반 클래스입니다.

#### 클래스 상수 (환경 설정 기반)

| 상수명 | 설명 | 타입 |
|--------|------|------|
| `REQUIRED_TEMPLATE_XLSX_COLUMNS` | 템플릿 XLSX 필수 컬럼 | List[str] |
| `REQUIRED_LADDER_CSV_COLUMNS` | 레더 CSV 필수 컬럼 | List[str] |
| `REQUIRED_COMMENT_CSV_COLUMNS` | 커멘트 CSV 필수 컬럼 | List[str] |
| `ALLOWED_LADDER_ZIP_EXTENSIONS` | 레더 ZIP 허용 확장자 | List[str] |
| `ALLOWED_TEMPLATE_XLSX_EXTENSIONS` | 템플릿 허용 확장자 | List[str] |
| `ALLOWED_COMMENT_CSV_EXTENSIONS` | 커멘트 허용 확장자 | List[str] |
| `TEMPLATE_XLSX_HEADER_ROW` | 템플릿 헤더 행 인덱스 | int |
| `LADDER_CSV_HEADER_ROW` | 레더 CSV 헤더 행 인덱스 | int |
| `COMMENT_CSV_HEADER_ROW` | 커멘트 CSV 헤더 행 인덱스 | int |

---

## 🔧 주요 메서드

### 1. `validate_files()` - 전체 파일 검증

**목적**: 3개 파일(레더 ZIP, 템플릿 XLSX, 커멘트 CSV)의 통합 검증

**시그니처**:
```python
@staticmethod
def validate_files(
    ladder_zip: UploadFile,
    classification_xlsx: UploadFile,
    comment_csv: UploadFile,
) -> Tuple[bool, List[Dict], List[str], List[str]]
```

**반환값**:
```python
(
    is_valid: bool,              # 전체 검증 성공 여부
    errors: List[Dict],          # 에러 목록 (구조화된 딕셔너리)
    warnings: List[str],         # 경고 메시지 목록
    checked_files: List[str]     # 검증 완료된 파일 목록
)
```

**검증 프로세스**:
1. ✅ ZIP 파일 검증
2. ✅ XLSX 파일 검증 및 Logic ID 추출
3. ✅ CSV 파일 검증
4. ✅ 교차 검증 (XLSX의 Logic ID ↔ ZIP 내부 파일)

**에러 구조**:
```python
[
    {
        "valid_name": "레더 ZIP 파일 검증",
        "error_list": ["에러 메시지 1", "에러 메시지 2"]
    },
    {
        "valid_name": "템플릿 XLSX 파일 검증",
        "error_list": ["에러 메시지"]
    }
]
```

---

### 2. `_validate_zip_file()` - ZIP 파일 검증

**목적**: 레더 ZIP 파일의 형식 및 내용 검증

**검증 항목**:
1. 파일 업로드 여부 확인
2. 파일 확장자 검증 (`.zip`, `.7z` 등)
3. ZIP 파일 무결성 검증 (`testzip()`)
4. 내부 파일 목록 추출 (시스템 파일 제외)
   - 제외 대상: `__MACOSX`, `.DS_Store`, 숨김 파일, 디렉토리

**반환값**:
```python
(
    errors: List[str],           # 에러 메시지
    warnings: List[str],         # 경고 메시지
    checked_files: List[str]     # ZIP 내부 파일명 리스트 (확장자 포함)
)
```

**예시**:
```python
# 정상 케이스
checked_files = ["MAIN_001.csv", "SUB_002.csv", "ALARM_003.csv"]

# 경고 발생 케이스
warnings = ["ZIP 파일에서 시스템 파일 5개 제외됨 (전체: 25개 → 유효: 20개)"]
```

---

### 3. `_validate_xlsx_file()` - XLSX 템플릿 검증

**목적**: 분류체계 템플릿 XLSX 파일 검증 및 Logic ID 추출

**검증 항목**:
1. 파일 업로드 여부 및 확장자 확인 (`.xlsx`, `.xls`)
2. 필수 컬럼 존재 여부 확인
3. **필수 컬럼의 결측값(NULL) 검증**
   - 결측값 발견 시 위치(행 번호) 포함하여 에러 반환
4. Logic ID 중복 검사
   - 중복 발견 시 상세 정보 제공

**반환값**:
```python
(
    errors: List[str],
    warnings: List[str],
    checked_files: List[str]     # Logic ID 리스트 (`.csv` 확장자 추가됨)
)
```

**Logic ID 처리**:
```python
# XLSX에서 추출
df["Logic ID"] = ["MAIN_001", "SUB_002", "SUB_002", "ALARM_003"]

# 중복 검사 후 에러 반환
errors = [
    "템플릿 XLSX 파일에 중복된 Logic ID가 있습니다. "
    "중복된 항목 1개: SUB_002"
]

# 정상 케이스 (중복 없음)
checked_files = ["MAIN_001.csv", "SUB_002.csv", "ALARM_003.csv"]
```

---

### 4. `_validate_csv_file()` - CSV 커멘트 검증

**목적**: 커멘트 CSV 파일 형식 검증

**검증 항목**:
1. 파일 업로드 여부 및 확장자 확인 (`.csv`)
2. 인코딩 자동 감지 (`utf-8` → `cp949` → `latin-1`)
3. 필수 컬럼 존재 여부 확인

**반환값**:
```python
(
    errors: List[str],
    warnings: List[str],
    checked_files: List[str]     # (현재는 빈 리스트)
)
```

---

### 5. `_validate_file_cross_reference()` - 교차 검증

**목적**: 템플릿 XLSX의 Logic ID와 ZIP 내부 파일 간 매칭 검증

**파라미터**:
```python
ladder_zip: UploadFile          # 레더 ZIP 파일
required_files: List[str]       # 템플릿에 명시된 파일 (Logic ID + .csv)
actual_files: List[str]         # ZIP 내부 실제 파일명
```

**검증 로직**:
```python
# 집합 연산
matched_files = required_set ∩ actual_set      # 매칭된 파일
missing_files = required_set - actual_set      # 누락된 파일 (에러)
extra_files = actual_set - required_set        # 불필요한 파일 (경고)

# 매칭된 파일별 내부 구조 검증
for csv_filename in matched_files:
    # ZIP 내부에서 파일 읽기
    # 헤더 컬럼 추출 (CSV reader 사용)
    # 필수 컬럼 확인
```

**반환값**:
```python
(
    errors: List[str],
    warnings: List[str],
    checked_files: List[str]     # 검증 완료된 파일명
)
```

**예시 결과**:
```python
# 에러 케이스
errors = [
    "분류체계 데이터에 있는 3개 파일이 ZIP 파일에 없습니다: "
    "MAIN_001.csv, SUB_002.csv, ALARM_003.csv"
]

# 경고 케이스
warnings = [
    "ZIP 파일에 불필요한 2개 파일이 포함되어 있습니다: "
    "OLD_FILE.csv, BACKUP.csv"
]

# 매칭된 파일의 컬럼 검증 에러
errors = [
    "매칭된 CSV 파일 'MAIN_001.csv'에 필수 컬럼이 없습니다: "
    "LOGIC_ID, DESCRIPTION"
]
```

---

## 📊 검증 플로우 다이어그램

```
validate_files()
    │
    ├─► _validate_zip_file()
    │       └─► ZIP 무결성 + 파일 목록 추출
    │           → zip_files: List[str]
    │
    ├─► _validate_xlsx_file()
    │       └─► 필수 컬럼 + Logic ID 중복 검사
    │           → xlsx_files: List[str] (Logic ID + .csv)
    │
    ├─► _validate_csv_file()
    │       └─► 필수 컬럼 검증
    │
    └─► _validate_file_cross_reference()
            ├─► 집합 연산 (매칭/누락/불필요)
            └─► 매칭된 파일 내부 구조 검증
                → checked_files: List[str]
```

---

## 🔍 주요 검증 규칙

### ZIP 파일 검증
- ✅ 허용 확장자: `.zip`, `.7z` (환경 설정 기반)
- ✅ ZIP 무결성 검사 (`testzip()`)
- ✅ 시스템 파일 자동 제외
  - `__MACOSX/` 디렉토리
  - `.DS_Store` 파일
  - 숨김 파일 (`.`로 시작)
  - 빈 디렉토리

### XLSX 템플릿 검증
- ✅ 필수 컬럼 존재 확인 (환경 설정 기반)
- ✅ **필수 컬럼 결측값 검증** (행 번호 포함)
- ✅ Logic ID 중복 검사
  - 중복 발견 시: 에러 + 상세 정보(warnings)
  - 중복 없음: `checked_files`에 추가

### CSV 커멘트 검증
- ✅ 인코딩 자동 감지 (3단계)
  1. `utf-8`
  2. `cp949` (한글 Windows 인코딩)
  3. `latin-1` (fallback)
- ✅ 필수 컬럼 확인

### 교차 검증
- ✅ 집합 연산으로 파일 매칭
- ✅ 매칭된 파일의 CSV 구조 검증
  - CSV reader로 헤더만 읽기 (성능 최적화)
  - 필수 컬럼 확인

---

## ⚠️ 에러 처리 패턴

### 조기 종료 (Early Return)
```python
# 타입 검증 실패 시 즉시 반환
if errors:
    return errors, warnings, checked_files
```

### 구조화된 에러 반환
```python
# validate_files()에서만 사용
if len(zip_errors) > 0:
    errors.append({
        "valid_name": "레더 ZIP 파일 검증",
        "error_list": zip_errors
    })
```

### 제한된 에러 표시
```python
# 10개 초과 시 개수만 표시
f"{', '.join(duplicates[:10])}" + 
(f" 외 {len(duplicates) - 10}개" if len(duplicates) > 10 else "")
```

---

## 🔧 사용 예시

### API 엔드포인트에서 호출
```python
from api.services.program_validator import ProgramValidator

# 파일 업로드 엔드포인트
@router.post("/register")
async def register_plc(
    ladder_zip: UploadFile,
    classification_xlsx: UploadFile,
    comment_csv: UploadFile
):
    # 검증 실행
    is_valid, errors, warnings, checked_files = (
        ProgramValidator.validate_files(
            ladder_zip,
            classification_xlsx,
            comment_csv
        )
    )
    
    # 검증 실패 시 에러 반환
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "파일 검증 실패",
                "errors": errors,
                "warnings": warnings
            }
        )
    
    # 성공 시 후속 처리
    logger.info(f"검증 완료: {len(checked_files)}개 파일")
    # ... S3 업로드 등 비즈니스 로직
```

---

## 🎯 성능 최적화

### 1. CSV 헤더 부분 읽기
```python
# 전체 CSV 파일을 읽지 않고 헤더만 추출
reader = csv.reader(io.StringIO(csv_text))
lines = []
for i, row in enumerate(reader):
    if i > header_row_index:
        break
    lines.append(row)

header_columns = lines[header_row_index]
```

**장점**:
- 대용량 CSV 파일 처리 시 메모리 효율성 향상
- 헤더 검증만 필요한 경우 불필요한 데이터 로딩 방지

### 2. 파일 포인터 복귀
```python
ladder_zip.file.seek(0)
zip_content = ladder_zip.file.read()
ladder_zip.file.seek(0)  # 필수: 다음 단계에서 재사용 가능
```

---

## 📝 개선 가능 영역

### 1. 타입 체크 코드 주석 처리
- 현재: 파일 타입 사전 검증 코드가 주석 처리됨
- 이유: 각 개별 검증 메서드 내부로 이동
- 제안: 주석 코드 제거 또는 히스토리 문서화

### 2. CSV 커멘트 파일 결측값 검증 부재
- XLSX는 필수 컬럼 결측값 검증 존재
- CSV는 컬럼 존재 여부만 확인
- 제안: CSV도 동일한 결측값 검증 로직 추가

### 3. 에러 구조 일관성
- `validate_files()`: 딕셔너리 구조
- 하위 메서드: 문자열 리스트
- 제안: 전체 일관된 구조 사용

---

## 🔗 연관 모듈

### 호출 위치
- `api/routers/plc.py` - `/register` 엔드포인트

### 의존 설정
- `config/simple_settings.py` - 환경 설정값

### 후속 처리
- S3 파일 업로드 서비스
- Prefect 파이프라인 트리거 (벡터 인덱싱)

---

## 📅 변경 이력

| 날짜 | 변경 내용 | 작성자 |
|------|----------|--------|
| 2025-11-18 | 기술 문서 초안 작성 | Ji-Yong |

---

## 📚 참고 자료

- FastAPI UploadFile: https://fastapi.tiangolo.com/tutorial/request-files/
- Pandas: https://pandas.pydata.org/docs/
- Python zipfile: https://docs.python.org/3/library/zipfile.html
