from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json
import re
import uuid
import hashlib
from loguru import logger

def generate_id() -> str:
    """고유 ID 생성"""
    return str(uuid.uuid4())

def generate_timestamp() -> str:
    """현재 타임스탬프 생성"""
    return datetime.utcnow().isoformat()

def hash_text(text: str) -> str:
    """텍스트 해시 생성"""
    return hashlib.sha256(text.encode()).hexdigest()

def truncate_text(text: str, max_length: int = 100) -> str:
    """텍스트 길이 제한"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_as_markdown(text: str) -> str:
    """텍스트를 마크다운 형식으로 변환"""
    return text

def format_as_json(data: Union[Dict, List]) -> str:
    """데이터를 JSON 형식으로 변환"""
    return json.dumps(data, ensure_ascii=False, indent=2)

def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """마크다운 텍스트에서 코드 블록 추출
    
    Args:
        text: 마크다운 텍스트
        
    Returns:
        코드 블록 목록 (언어, 코드)
    """
    # 코드 블록 패턴: ```언어\n코드\n```
    pattern = r"```([\w-]*)\n([\s\S]*?)\n```"
    matches = re.findall(pattern, text)
    
    code_blocks = []
    for language, code in matches:
        code_blocks.append({
            "language": language.strip() or "text",
            "code": code
        })
    
    return code_blocks

def extract_urls(text: str) -> List[str]:
    """텍스트에서 URL 추출"""
    # URL 패턴
    pattern = r"https?://[^\s)]+"
    return re.findall(pattern, text)

def sanitize_input(text: str) -> str:
    """입력 텍스트 정제"""
    # HTML 태그 제거
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()

def merge_metadata(metadata1: Dict[str, Any], metadata2: Dict[str, Any]) -> Dict[str, Any]:
    """메타데이터 병합"""
    result = metadata1.copy()
    for key, value in metadata2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_metadata(result[key], value)
        else:
            result[key] = value
    return result

def calculate_token_count(text: str) -> int:
    """텍스트의 대략적인 토큰 수 계산
    
    영어 기준으로 단어 수의 약 1.3배가 토큰 수
    """
    # 간단한 구현: 공백으로 분할한 단어 수 * 1.3
    return int(len(text.split()) * 1.3)

def parse_json_string(json_str: str) -> Dict[str, Any]:
    """JSON 문자열 파싱"""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {str(e)}")
        return {}

def format_error_response(error_message: str, status_code: int = 400) -> Dict[str, Any]:
    """오류 응답 형식화"""
    return {
        "error": {
            "message": error_message,
            "status_code": status_code,
            "timestamp": generate_timestamp()
        }
    }

def chunk_text(text: str, chunk_size: int = 1000) -> List[str]:
    """텍스트를 청크로 분할"""
    # 문장 단위로 분할
    sentences = re.split(r"(?<=[.!?])\s+", text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # 현재 청크에 문장 추가 시 청크 크기 초과 여부 확인
        if len(current_chunk) + len(sentence) + 1 > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
    
    # 마지막 청크 추가
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks