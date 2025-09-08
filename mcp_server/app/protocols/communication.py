from typing import Dict, Any, List, Optional
from loguru import logger

from app.protocols.base import BaseProtocol
from app.services.llm import LLMService

class CommunicationProtocol(BaseProtocol):
    """커뮤니케이션 프로토콜 (FR-501)
    
    생성된 콘텐츠를 사용자에게 효과적으로 전달하기 위한 형식과 스타일을 적용합니다.
    """
    
    def __init__(self):
        super().__init__()
        self.llm_service = LLMService()
    
    async def execute(self, content: str, prompt: str, context: Dict[str, Any]) -> str:
        """프로토콜 실행 메서드
        
        Args:
            content: 원본 콘텐츠
            prompt: 사용자 프롬프트
            context: 실행 컨텍스트
            
        Returns:
            형식화된 응답
        """
        return await self.format_response(content, prompt, context)
    
    async def format_response(self, content: str, prompt: str, context: Dict[str, Any], api_key: Optional[str] = None) -> str:
        """응답 형식화 메서드
        
        Args:
            content: 원본 콘텐츠
            prompt: 사용자 프롬프트
            context: 실행 컨텍스트
            
        Returns:
            형식화된 응답
        """
        try:
            # 형식화 시작 로그
            self.log_execution("formatting_start", {
                "content_length": len(content),
                "format": context.get("format", "text")
            })
            
            # 형식 확인
            output_format = context.get("format", "text")
            
            # API 키가 제공된 경우 새 LLM 서비스 인스턴스 생성
            llm_service = LLMService(api_key=api_key) if api_key else self.llm_service
            
            # 형식에 따른 처리
            if output_format == "json":
                formatted_response = await self._format_as_json(content, context)
            elif output_format == "markdown":
                formatted_response = await self._format_as_markdown(content, context)
            elif output_format == "code":
                formatted_response = await self._format_as_code(content, context)
            elif output_format == "table":
                formatted_response = await self._format_as_table(content, context)
            else:  # 기본 텍스트 형식
                formatted_response = await self._format_as_text(content, context)
            
            # 인용 및 출처 추가
            if context.get("add_citations", False) and context.get("sources"):
                formatted_response = self._add_citations(formatted_response, context.get("sources", []), output_format)
            
            # 형식화 완료 로그
            self.log_execution("formatting_complete", {
                "original_length": len(content),
                "formatted_length": len(formatted_response),
                "format": output_format
            })
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"Response formatting failed: {str(e)}")
            self.log_execution("formatting_error", {"error": str(e)})
            # 오류 발생 시 원본 콘텐츠 반환
            return content
    
    async def _format_as_text(self, content: str, context: Dict[str, Any]) -> str:
        """텍스트 형식으로 변환"""
        # 기본 텍스트 형식은 단락 구분과 가독성 향상에 중점
        
        # 단락 구분 확인 및 수정
        if "\n\n" not in content:
            # 단락 구분이 없는 경우 문장 단위로 구분
            sentences = content.split(". ")
            paragraphs = []
            current_paragraph = []
            
            for sentence in sentences:
                current_paragraph.append(sentence)
                if len(current_paragraph) >= 3:  # 3문장마다 단락 구분
                    paragraphs.append(". ".join(current_paragraph) + ".")
                    current_paragraph = []
            
            if current_paragraph:  # 남은 문장 처리
                paragraphs.append(". ".join(current_paragraph) + ".")
            
            content = "\n\n".join(paragraphs)
        
        # 가독성 향상을 위한 추가 처리
        tone = context.get("tone", "neutral")
        if tone == "conversational":
            # 대화체 스타일 적용
            prompt = f"""다음 텍스트를 더 대화체 스타일로 변환하세요. 친근하고 자연스러운 어조를 유지하되, 내용은 그대로 유지하세요:

{content}"""
            
            try:
                content = await llm_service.generate_text(
                    prompt=prompt,
                    max_tokens=len(content) + 100,
                    temperature=0.4
                )
            except Exception as e:
                logger.warning(f"Conversational tone formatting failed: {str(e)}")
        
        return content
    
    async def _format_as_markdown(self, content: str, context: Dict[str, Any]) -> str:
        """마크다운 형식으로 변환"""
        prompt = f"""다음 텍스트를 마크다운 형식으로 변환하세요. 적절한 제목, 부제목, 목록, 강조, 인용 등의 마크다운 요소를 사용하여 가독성을 높이세요:

{content}"""
        
        try:
            markdown_content = await llm_service.generate_text(
                prompt=prompt,
                max_tokens=len(content) + 200,
                temperature=0.3
            )
            return markdown_content
        except Exception as e:
            logger.warning(f"Markdown formatting failed: {str(e)}")
            # 기본 마크다운 형식 적용
            lines = content.split("\n")
            if lines:
                # 첫 줄을 제목으로 설정
                lines[0] = f"# {lines[0]}"
            
            # 단락에 빈 줄 추가
            formatted_lines = []
            for line in lines:
                formatted_lines.append(line)
                formatted_lines.append("")
            
            return "\n".join(formatted_lines)
    
    async def _format_as_json(self, content: str, context: Dict[str, Any]) -> str:
        """JSON 형식으로 변환"""
        prompt = f"""다음 텍스트를 유효한 JSON 형식으로 변환하세요. 적절한 키와 값을 사용하여 구조화된 데이터로 표현하세요:

{content}"""
        
        try:
            json_content = await llm_service.generate_text(
                prompt=prompt,
                max_tokens=len(content) + 200,
                temperature=0.2,
                options={"format": "json"}
            )
            return json_content
        except Exception as e:
            logger.warning(f"JSON formatting failed: {str(e)}")
            # 기본 JSON 형식 적용
            import json
            try:
                return json.dumps({"content": content})
            except:
                return f"{{\"content\": \"{content.replace('"', '\\"')}\"}}"
    
    async def _format_as_code(self, content: str, context: Dict[str, Any]) -> str:
        """코드 형식으로 변환"""
        language = context.get("code_language", "python")
        
        prompt = f"""다음 텍스트를 {language} 코드로 변환하세요. 실행 가능하고 가독성 높은 코드를 작성하세요:

{content}"""
        
        try:
            code_content = await llm_service.generate_text(
                prompt=prompt,
                max_tokens=len(content) + 200,
                temperature=0.2
            )
            return f"```{language}\n{code_content}\n```"
        except Exception as e:
            logger.warning(f"Code formatting failed: {str(e)}")
            # 기본 코드 블록 형식 적용
            return f"```{language}\n{content}\n```"
    
    async def _format_as_table(self, content: str, context: Dict[str, Any]) -> str:
        """테이블 형식으로 변환"""
        prompt = f"""다음 텍스트를 마크다운 테이블 형식으로 변환하세요. 데이터를 행과 열로 구조화하여 표현하세요:

{content}"""
        
        try:
            table_content = await llm_service.generate_text(
                prompt=prompt,
                max_tokens=len(content) + 300,
                temperature=0.3
            )
            return table_content
        except Exception as e:
            logger.warning(f"Table formatting failed: {str(e)}")
            # 기본 텍스트 반환
            return content
    
    def _add_citations(self, content: str, sources: List[str], output_format: str) -> str:
        """인용 및 출처 추가"""
        if not sources:
            return content
        
        # 출처 목록 생성
        sources_text = "\n".join([f"{i+1}. {source}" for i, source in enumerate(sources)])
        
        if output_format == "markdown":
            # 마크다운 형식 인용
            return f"{content}\n\n---\n\n**출처:**\n{sources_text}"
        elif output_format == "json":
            # JSON에 출처 필드 추가 시도
            try:
                import json
                content_json = json.loads(content)
                content_json["sources"] = sources
                return json.dumps(content_json)
            except:
                # JSON 파싱 실패 시 텍스트 형식으로 추가
                return f"{content}\n\n출처:\n{sources_text}"
        else:
            # 기본 텍스트 형식 인용
            return f"{content}\n\n출처:\n{sources_text}"