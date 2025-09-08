from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from loguru import logger

class BaseProtocol(ABC):
    """MCP 프로토콜의 기본 추상 클래스
    
    모든 MCP 프로토콜은 이 클래스를 상속받아 구현해야 합니다.
    """
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.metadata = {}
        self.execution_log = []
        logger.info(f"Initializing protocol: {self.name}")
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """프로토콜 실행 메서드
        
        모든 프로토콜은 이 메서드를 구현해야 합니다.
        """
        pass
    
    def log_execution(self, step: str, data: Dict[str, Any]) -> None:
        """프로토콜 실행 로그 기록
        
        Args:
            step: 실행 단계 이름
            data: 로그 데이터
        """
        log_entry = {
            "protocol": self.name,
            "step": step,
            "data": data,
            "timestamp": self._get_timestamp()
        }
        self.execution_log.append(log_entry)
        logger.debug(f"Protocol {self.name} - Step {step}: {data}")
    
    def get_execution_log(self) -> List[Dict[str, Any]]:
        """프로토콜 실행 로그 반환"""
        return self.execution_log
    
    def set_metadata(self, key: str, value: Any) -> None:
        """메타데이터 설정"""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """메타데이터 조회"""
        return self.metadata.get(key, default)
    
    def get_all_metadata(self) -> Dict[str, Any]:
        """모든 메타데이터 반환"""
        return self.metadata
    
    def _get_timestamp(self) -> str:
        """현재 타임스탬프 반환"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def __str__(self) -> str:
        return f"{self.name} Protocol"
    
    def __repr__(self) -> str:
        return f"<{self.name} Protocol at {hex(id(self))}>"