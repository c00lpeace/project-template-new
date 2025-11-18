# _*_ coding: utf-8 _*_
"""Program validation module for file validation."""
import csv
import io
import logging
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
from fastapi import UploadFile
from src.config.simple_settings import settings

logger = logging.getLogger(__name__)


class ProgramValidator:
    """프로그램 파일 유효성 검사 클래스"""

    REQUIRED_TEMPLATE_XLSX_COLUMNS = settings.get_pgm_template_required_columns()   # 프로그램 템플릿 XLSX 필수 컬럼
    REQUIRED_LADDER_CSV_COLUMNS = settings.get_pgm_ladder_csv_required_columns()    # 프로그램 레더 CSV 필수 컬럼
    REQUIRED_COMMENT_CSV_COLUMNS = settings.get_pgm_comment_csv_required_columns()  # 프로그램 커멘트 CSV 필수 컬럼

    ALLOWED_LADDER_ZIP_EXTENSIONS = settings.get_pgm_ladder_zip_allowed_extensions()    # 레더 ZIP 허용 확장자
    ALLOWED_TEMPLATE_XLSX_EXTENSIONS = settings.get_pgm_template_allowed_extensions()   # 템플릿 XLSX 허용 확장자
    ALLOWED_COMMENT_CSV_EXTENSIONS = settings.get_pgm_comment_csv_allowed_extensions()  # 커멘트 CSV 허용 확장자

    TEMPLATE_XLSX_HEADER_ROW = settings.pgm_template_xlsx_header_row  # 템플릿 XLSX 헤더 행 인덱스
    LADDER_CSV_HEADER_ROW = settings.pgm_ladder_csv_header_row        # 레더 CSV 헤더 행 인덱스
    COMMENT_CSV_HEADER_ROW = settings.pgm_comment_csv_header_row      # 커멘트 CSV 헤더 행 인덱스

    @staticmethod
    def validate_files(
        ladder_zip: UploadFile,
        classification_xlsx: UploadFile,
        comment_csv: UploadFile,
    ) -> Tuple[bool, List[Dict], List[str], List[str]]: 
        """
        파일 유효성 검사

        Returns:
            Tuple[bool, List[str], List[str], List[str]]:
                (is_valid, errors, warnings, checked_files)
        """
        errors = []
        warnings = []
        checked_files = []

        try:
            # # 1. 파일 타입 사전 검증
            # # 레더 ZIP 파일 타입 체크
            # if not ladder_zip or not ladder_zip.filename:
            #     errors.append("레더 ZIP 파일이 업로드되지 않았습니다.")
            # elif not ladder_zip.filename.lower().endswith((".zip", ".7z")):
            #     errors.append(
            #         f"레더 파일은 압축파일 형식이어야 합니다(.zip, .7z). "
            #         f"업로드된 파일: {ladder_zip.filename}"
            #     )

            # # 분류체계 XLSX 파일 타입 체크
            # if not classification_xlsx or not classification_xlsx.filename:
            #     errors.append("분류체계 파일이 업로드되지 않았습니다.")
            # elif not classification_xlsx.filename.lower().endswith((".xlsx", ".xls")):
            #     errors.append(
            #         f"분류체계 파일은 Excel 형식이어야 합니다(.xlsx, .xls). "
            #         f"업로드된 파일: {classification_xlsx.filename}"
            #     )

            # # 커멘트 CSV 파일 타입 체크
            # if not comment_csv or not comment_csv.filename:
            #     errors.append("커멘트 파일이 업로드되지 않았습니다.")
            # elif not comment_csv.filename.lower().endswith(".csv"):
            #     errors.append(
            #         f"커멘트 파일은 CSV 형식이어야 합니다(.csv). "
            #         f"업로드된 파일: {comment_csv.filename}"
            #     )

            # # 타입 검증 실패 시 조기 종료
            # if errors:
            #     return False, errors, warnings, checked_files

            # 1. ZIP 파일 검증
            zip_errors, zip_warnings, zip_files = ProgramValidator._validate_zip_file(
                ladder_zip
            )
            # errors.extend(zip_errors)
            if len(zip_errors) > 0:
                errors.append({"valid_name": "레더 ZIP 파일 검증", "error_list": zip_errors})
            warnings.extend(zip_warnings)
            # zip_files: 레더 Zip 내부 파일명 리스트(확장자 제외)
            # checked_files.extend(zip_files)

            # 2. XLSX 파일 검증 및 컬럼 확인
            xlsx_errors, xlsx_warnings, xlsx_files = (
                ProgramValidator._validate_xlsx_file(classification_xlsx)
            )
            # errors.extend(xlsx_errors)
            if len(xlsx_errors) > 0:
                errors.append({"valid_name": "템플릿 XLSX 파일 검증", "error_list": xlsx_errors})
            warnings.extend(xlsx_warnings)
            # xlsx_files: 템플릿 XLSX의 Logic ID 리스트
            checked_files.extend(xlsx_files)

            # 3. CSV 파일 검증 및 컬럼 확인
            csv_errors, csv_warnings, csv_files = ProgramValidator._validate_csv_file(
                comment_csv
            )
            # errors.extend(csv_errors)
            if len(csv_errors) > 0:
                errors.append({"valid_name": "커멘트 CSV 파일 검증", "error_list": csv_errors})
            warnings.extend(csv_warnings)
            # checked_files.extend(csv_files)

            # 4. XLSX의 로직파일명이 ZIP에 있는지 확인(수정 중 - checked_files 값 사용)
            # if not errors:  # 에러가 없을 때만 교차 검증
            if not errors and len(xlsx_files)>0 and len(zip_files)>0:  # 에러가 없을 때만 교차 검증 (그리고 파일 리스트가 비어있지 않을 때)
                # cross_errors = ProgramValidator._validate_file_cross_reference(
                #     ladder_zip, classification_xlsx
                # )
                cross_errors, cross_warnings, checked_files = ProgramValidator._validate_file_cross_reference(
                    ladder_zip, zip_files, xlsx_files
                )
                if len(cross_errors) > 0:
                    errors.append({"valid_name": "템플릿 파일-레더 ZIP 파일 교차 검증", "error_list": cross_errors})
                warnings.extend(cross_warnings)

            is_valid = len(errors) == 0

            return is_valid, errors, warnings, checked_files

        except Exception as e:
            logger.error(f"유효성 검사 중 예외 발생: {str(e)}")
            errors.append(f"유효성 검사 중 오류 발생: {str(e)}")
            return False, errors, warnings, checked_files

    @staticmethod
    def _validate_zip_file(
        zip_file: UploadFile,
    ) -> Tuple[List[str], List[str], List[str]]:
        """ZIP 파일 유효성 검사"""
        errors = []
        warnings = []
        checked_files = []

        try:
            # 환경변수로부터 허용된 확장자 불러오기
            allowed_extensions = tuple(ProgramValidator.ALLOWED_LADDER_ZIP_EXTENSIONS)

            # 레더 ZIP 파일 타입 체크
            if not zip_file or not zip_file.filename:
                errors.append("레더 ZIP 파일이 업로드되지 않았습니다.")
            elif not zip_file.filename.lower().endswith(allowed_extensions):
                errors.append(
                    f"레더 ZIP 파일은 압축파일 형식이어야 합니다({', '.join(allowed_extensions)}). "
                    f"업로드된 파일: {zip_file.filename}"
                )
            # 타입 검증 실패 시 조기 종료
            if errors:
                return errors, warnings, checked_files
            
            # 파일 읽기
            zip_file.file.seek(0)
            zip_content = zip_file.file.read()
            zip_file.file.seek(0)

            # ZIP 파일 형식 확인
            if not zipfile.is_zipfile(io.BytesIO(zip_content)):
                errors.append(f"{zip_file.filename}은(는) 유효한 ZIP 파일이 아닙니다.")
                return errors, warnings, checked_files

            # ZIP 파일 내용 확인
            with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zip_ref:
                # ZIP 파일 무결성 검증
                bad_file = zip_ref.testzip()
                if bad_file:
                    errors.append(
                        f"{zip_file.filename}이(가) 손상되었습니다. "
                        f"손상된 파일: {bad_file}"
                    )
                    return errors, warnings, checked_files
                
                # 파일 목록 추출 (디렉토리 및 시스템 파일 제외)
                all_files = [
                    name for name in zip_ref.namelist()
                    if not name.endswith("/")  # 디렉토리 제외
                    and not name.startswith("__MACOSX")  # macOS 메타데이터 제외
                    and "/.DS_Store" not in name  # macOS 설정파일 제외
                    and not name.startswith(".")  # 숨김 파일 제외
                ]

                # 파일명만 추출 (경로 및 확장자 제외)
                file_list = []
                for file_path in all_files:
                    # 경로에서 파일명만 추출
                    filename = Path(file_path).name
                    # 확장자 제거
                    # name_without_ext = Path(filename).stem
                    file_list.append(filename)

                # # 파일 목록 추출 (디렉토리 및 시스템 파일 제외)
                # all_files = zip_ref.namelist()
                # file_list = [
                #     Path(name).name
                #     for name in all_files
                #     if not name.endswith("/")  # 디렉토리 제외
                #     and not name.startswith("__MACOSX")  # macOS 메타데이터 제외
                #     and "/.DS_Store" not in name  # macOS 설정파일 제외
                #     and not name.startswith(".")  # 숨김 파일 제외
                # ]
                checked_files = file_list

                # 필터링된 파일이 있으면 경고 추가
                filtered_count = len(all_files) - len(file_list)
                if filtered_count > 0:
                    warnings.append(
                        f"ZIP 파일에서 시스템 파일 {filtered_count}개 제외됨 "
                        f"(전체: {len(all_files)}개 → 유효: {len(file_list)}개)"
                    )

                if len(file_list) == 0:
                    errors.append(f"{zip_file.filename}은(는) 비어있는 ZIP 파일입니다.")                    
                else:
                    logger.info(f"ZIP 파일 검증 완료: {len(file_list)}개 파일 발견")

        except Exception as e:
            errors.append(f"ZIP 파일 검증 중 오류: {str(e)}")

        return errors, warnings, checked_files

    @staticmethod
    def _validate_xlsx_file(
        xlsx_file: UploadFile,
    ) -> Tuple[List[str], List[str], List[str]]:
        """XLSX 파일 유효성 검사 및 컬럼 확인"""
        errors = []
        warnings = []
        checked_files = []

        try:
            # 환경변수로부터 허용된 확장자 및 필수 컬럼 불러오기
            allowed_extensions = tuple(ProgramValidator.ALLOWED_TEMPLATE_XLSX_EXTENSIONS)
            header_row_index = ProgramValidator.TEMPLATE_XLSX_HEADER_ROW
            required_columns = ProgramValidator.REQUIRED_TEMPLATE_XLSX_COLUMNS
            
            # 분류체계 XLSX 파일 타입 체크
            if not xlsx_file or not xlsx_file.filename:
                errors.append("분류체계 파일이 업로드되지 않았습니다.")
            elif not xlsx_file.filename.lower().endswith(allowed_extensions):
                errors.append(
                    f"분류체계 파일은 Excel 형식이어야 합니다({', '.join(allowed_extensions)}). "
                    f"업로드된 파일: {xlsx_file.filename}"
                )
            # 파일 읽기
            xlsx_file.file.seek(0)
            xlsx_content = xlsx_file.file.read()
            xlsx_file.file.seek(0)

            # XLSX 파일 읽기
            df = pd.read_excel(io.BytesIO(xlsx_content))

            # 필수 컬럼 확인
            missing_columns = []
            for col in required_columns:
                if col not in df.columns:
                    missing_columns.append(col)
                # 필수컬럼의 공백값 확인
                else:
                    # 결측값 유무 확인
                    has_null = df[col].isnull().any()
                    if has_null:
                        null_count = df[col].isnull().sum()  # 결측값 개수
                        null_rows_index = df[df[col].isnull()].index  # 결측값 행 인덱스 리스트
                        excel_row_numbers = [idx + header_row_index + 2 for idx in null_rows_index] # 엑셀 행 번호 계산 (헤더 행 및 1-based 인덱스 고려)
                        errors.append(
                            f"템플릿 XLSX 파일의 필수 컬럼 '{col}'에 {null_count}개의 결측값이 있습니다. "
                            f"(행 위치: {excel_row_numbers})"
                        )
                

            if missing_columns:
                errors.append(
                    f"XLSX 파일에 필수 컬럼이 없습니다: {', '.join(missing_columns)}. "
                    f"현재 컬럼: {', '.join(df.columns.tolist())}"
                )
            else:
                # 로직파일명 리스트 추출
                if "Logic ID" in df.columns:
                    # 1. 모든 Logic ID 추출 (NaN 제외, 문자열 변환)
                    logic_files_all = df["Logic ID"].dropna().astype(str).tolist()

                    # 2. 고유한 Logic ID 추출
                    logic_files_unique = (
                        df["Logic ID"].dropna().astype(str).unique().tolist()
                    )

                    # 3. 중복 검사
                    if len(logic_files_all) != len(logic_files_unique):
                        # 중복된 값 찾기
                        from collections import Counter

                        counts = Counter(logic_files_all)
                        duplicates = [
                            item for item, count in counts.items() if count > 1
                        ]

                        errors.append( # 중복된 컬럼 10개 미만으로 표시(10개 초과 시 개수만 표시)
                            f"템플릿 XLSX 파일에 중복된 Logic ID가 있습니다. "
                            f"중복된 항목 {len(duplicates)}개: {', '.join(duplicates[:10])}"
                            + (f" 외 {len(duplicates) - 10}개" if len(duplicates) > 10 else "")
                        )

                        # 중복 상세 정보를 warnings에 추가
                        for dup in duplicates[:5]:  # 처음 5개만
                            dup_count = counts[dup]
                            warnings.append(f"  Logic ID '{dup}'가 {dup_count}번 중복됨")
                    else:
                        # 중복이 없을 때만 checked_files에 추가
                        checked_files = [f"{f}.csv" for f in logic_files_unique]
                        logger.info(
                            f"XLSX 파일 검증 완료: Logic ID {len(logic_files_unique)}개 확인"
                        )
                else:
                    errors.append("XLSX 파일에 'Logic ID' 컬럼을 찾을 수 없습니다.")


        except Exception as e:
            errors.append(f"XLSX 파일 검증 중 오류: {str(e)}")

        return errors, warnings, checked_files

    @staticmethod
    def _validate_csv_file(
        csv_file: UploadFile,
    ) -> Tuple[List[str], List[str], List[str]]:
        """CSV 파일 유효성 검사 및 컬럼 확인"""
        errors = []
        warnings = []
        checked_files = []

        try:
            # 환경변수로부터 허용된 확장자 및 헤더 위치, 필수 컬럼 불러오기
            allowed_extensions = tuple(ProgramValidator.ALLOWED_COMMENT_CSV_EXTENSIONS)
            header_row_index = ProgramValidator.COMMENT_CSV_HEADER_ROW
            required_columns = ProgramValidator.REQUIRED_COMMENT_CSV_COLUMNS

            # 커멘트 CSV 파일 타입 체크
            if not csv_file or not csv_file.filename:
                errors.append("커멘트 파일이 업로드되지 않았습니다.")
            elif not csv_file.filename.lower().endswith(allowed_extensions):
                errors.append(
                    f"커멘트 파일은 CSV 형식이어야 합니다({', '.join(allowed_extensions)}). "
                    f"업로드된 파일: {csv_file.filename}"
                )

            # 파일 읽기
            csv_file.file.seek(0)
            csv_content = csv_file.file.read()
            csv_file.file.seek(0)

            # CSV 파일 읽기 (인코딩 자동 감지 시도)
            try:
                df = pd.read_csv(io.BytesIO(csv_content), encoding="utf-8", header=header_row_index)
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(io.BytesIO(csv_content), encoding="cp949", header=header_row_index)
                except:
                    df = pd.read_csv(io.BytesIO(csv_content), encoding="latin-1", header=header_row_index)

            # 필수 컬럼 확인
            missing_columns = []
            for col in required_columns:
                if col not in df.columns:
                    missing_columns.append(col)

            if missing_columns:
                errors.append(
                    f"커멘트 CSV 파일에 필수 컬럼이 없습니다: {', '.join(missing_columns)}. "
                    f"현재 컬럼: {', '.join(df.columns.tolist())}"
                )
            else:
                logger.info(
                        f"커멘트 CSV 파일 검증 완료"
                    )

        except Exception as e:
            errors.append(f"커멘트 CSV 파일 검증 중 오류: {str(e)}")

        return errors, warnings, checked_files

    @staticmethod
    def _validate_file_cross_reference(
        ladder_zip: UploadFile,
        required_files: list[str],
        actual_files: list[str]
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        XLSX의 Logic ID 값의 파일이 ZIP 파일 내부에 실제로 있는지 교차 검증

         Args:
            ladder_zip: 업로드된 레더 ZIP 파일
            required_files: 템플릿에 명시된 필수 파일 리스트(Logic ID값 + .csv)
            actual_files: ZIP 내부 파일명 리스트
        """
        errors = []
        warnings = []
        checked_files = []

        try:
            # 집합 연산
            required_set = set(required_files)
            actual_set = set(actual_files)
            
            matched_files = list(required_set & actual_set)  # 교집합
            missing_files = list(required_set - actual_set)  # 필수이지만 누락된 파일
            extra_files = list(actual_set - required_set)    # 불필요한 파일

            if missing_files: # 누락된 파일 목록(에러)
                errors.append(
                    f"분류체계 데이터에 있는 {len(missing_files)}개 파일이 ZIP 파일에 없습니다: "
                    f"{', '.join(missing_files[:10])}"  # 처음 10개만 표시
                )
            if extra_files: # 불필요한 파일 목록(경고)
                warnings.append(
                    f"ZIP 파일에 불필요한 {len(extra_files)}개 파일이 포함되어 있습니다: "
                    f"{', '.join(extra_files[:10])}"  # 처음 10개만 표시
                )

            # ZIP 파일 내용 읽기
            ladder_zip.file.seek(0)
            zip_content = ladder_zip.file.read()
            ladder_zip.file.seek(0)  # 필수: 파일 포인터 복귀

            # 환경변수로부터 필수 컬럼 불러오기            
            required_columns = ProgramValidator.REQUIRED_LADDER_CSV_COLUMNS
            header_row_index = ProgramValidator.LADDER_CSV_HEADER_ROW

            # ZIP 파일 열기
            with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_ref:

                unavailable_files = []

                # 매칭된 파일만 검증
                for csv_filename in matched_files:
                    # ZIP 내부에서 파일 찾기 (경로 고려)
                    matching_paths = [
                        name for name in zip_ref.namelist()
                        if name.endswith(csv_filename) and not name.startswith('__MACOSX') # and 조건 추가..
                    ]
                    
                    if not matching_paths:
                        # 확인할 수 없는 파일
                        unavailable_files.append(csv_filename)
                        continue
                    
                    # 첫 번째 매칭 파일 사용
                    csv_path_in_zip = matching_paths[0]
                    
                    # CSV 파일 내용 읽기
                    csv_content = zip_ref.read(csv_path_in_zip)
                    
                    # 구조 검증
                    csv_text = csv_content.decode('utf-8', errors='ignore')

                    # CSV reader로 필요한 줄만 읽기
                    reader = csv.reader(io.StringIO(csv_text))
                    lines = []

                    for i, row in enumerate(reader):
                        # 헤더가 위치한 행까지 읽기
                        if i > header_row_index:
                            break
                        lines.append(row)
                    
                    # 헤더 컬럼 추출
                    header_columns = lines[header_row_index]
                    
                    # 필수 컬럼 확인
                    missing_columns = [col for col in required_columns if col not in header_columns]

                    if missing_columns:
                        errors.append(
                            f"매칭된 CSV 파일 '{csv_filename}'에 필수 컬럼이 없습니다: {', '.join(missing_columns)}. "
                            f"현재 컬럼: {', '.join(header_columns.tolist())}"
                        )

                    # if missing_cols: # 필수 컬럼 누락 시 에러 추가
                    #     errors.append(
                    #         f"매칭된 CSV 파일 '{csv_filename}'에 필수 컬럼이 없습니다: "
                    #         f"{', '.join(missing_cols)}."
                    #     )
                    else: # 검증 완료된 파일 리스트에 추가
                        checked_files.append(csv_filename)
                  
            if unavailable_files:
                errors.append(
                    f"다음 파일들은 ZIP 내부에서 찾을 수 없습니다: "
                    f"{', '.join(unavailable_files[:10])}"  # 처음 10개만 표시
                )
            else:
                logger.info(f"교차 검증 완료: {len(required_files)}개 파일 중 {len(checked_files)}개 확인됨")

        except Exception as e:
            errors.append(f"교차 검증 중 오류: {str(e)}")

        return errors, warnings, checked_files
