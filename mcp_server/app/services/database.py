from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os
from dotenv import load_dotenv
from loguru import logger

# 환경 변수 로드
load_dotenv()

# 데이터베이스 URL 가져오기
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# SQLAlchemy 설정
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 메타데이터 객체 생성
metadata = MetaData()

# 피드백 테이블 정의
feedback = Table(
    "feedback",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", String(50), nullable=True),
    Column("session_id", String(50), nullable=False),
    Column("feedback_type", String(20), nullable=False),
    Column("content", Text, nullable=False),
    Column("rating", Integer, nullable=True),
    Column("metadata", JSON, nullable=True),
    Column("created_at", DateTime, default=datetime.utcnow),
)

# 학습 메트릭 테이블 정의
learning_metrics = Table(
    "learning_metrics",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("metric_type", String(50), nullable=False),
    Column("value", JSON, nullable=False),
    Column("created_at", DateTime, default=datetime.utcnow),
)

# 대화 맥락 테이블 정의
conversation_context = Table(
    "conversation_context",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("session_id", String(50), nullable=False, unique=True),
    Column("messages", JSON, nullable=True),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow),
)

# 데이터베이스 초기화 함수
def init_db():
    metadata.create_all(bind=engine)


class DatabaseService:
    """데이터베이스 서비스 클래스
    
    SQLAlchemy를 사용하여 데이터베이스 작업을 처리합니다.
    """
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        
    def get_session(self) -> Session:
        """데이터베이스 세션을 반환합니다."""
        return self.SessionLocal()
    
    async def insert_data(self, collection: str, data: Dict[str, Any]) -> int:
        """데이터를 지정된 컬렉션에 삽입합니다.
        
        Args:
            collection: 데이터를 삽입할 컬렉션/테이블 이름
            data: 삽입할 데이터
            
        Returns:
            삽입된 데이터의 ID
        """
        try:
            session = self.get_session()
            table = metadata.tables.get(collection)
            
            if not table:
                logger.error(f"테이블 {collection}이(가) 존재하지 않습니다.")
                return -1
            
            # 현재 시간 추가
            if "created_at" not in data:
                data["created_at"] = datetime.utcnow()
                
            # 데이터 삽입
            result = session.execute(table.insert().values(**data))
            session.commit()
            
            return result.inserted_primary_key[0]
        except Exception as e:
            logger.error(f"데이터 삽입 중 오류 발생: {str(e)}")
            session.rollback()
            return -1
        finally:
            session.close()
    
    async def find_data(self, collection: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """지정된 쿼리로 데이터를 검색합니다.
        
        Args:
            collection: 검색할 컬렉션/테이블 이름
            query: 검색 쿼리
            
        Returns:
            검색된 데이터 목록
        """
        try:
            session = self.get_session()
            table = metadata.tables.get(collection)
            
            if not table:
                logger.error(f"테이블 {collection}이(가) 존재하지 않습니다.")
                return []
            
            # 쿼리 구성
            stmt = table.select()
            for key, value in query.items():
                if hasattr(table.c, key):
                    stmt = stmt.where(getattr(table.c, key) == value)
            
            # 쿼리 실행
            result = session.execute(stmt)
            rows = result.fetchall()
            
            # 결과를 딕셔너리 목록으로 변환
            return [dict(row._mapping) for row in rows]
        except Exception as e:
            logger.error(f"데이터 검색 중 오류 발생: {str(e)}")
            return []
        finally:
            session.close()
    
    async def update_data(self, collection: str, query: Dict[str, Any], update_data: Dict[str, Any]) -> int:
        """지정된 쿼리로 데이터를 업데이트합니다.
        
        Args:
            collection: 업데이트할 컬렉션/테이블 이름
            query: 업데이트할 데이터를 찾기 위한 쿼리
            update_data: 업데이트할 데이터
            
        Returns:
            업데이트된 레코드 수
        """
    
    async def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """지정된 쿼리로 단일 데이터를 검색합니다.
        
        Args:
            collection: 검색할 컬렉션/테이블 이름
            query: 검색 쿼리
            
        Returns:
            검색된 데이터 또는 None
        """
        try:
            results = await self.find_data(collection, query)
            return results[0] if results else None
        except Exception as e:
            logger.error(f"단일 데이터 검색 중 오류 발생: {str(e)}")
            return None
    
    async def upsert(self, collection: str, query: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """지정된 쿼리로 데이터를 업서트(업데이트 또는 삽입)합니다.
        
        Args:
            collection: 업서트할 컬렉션/테이블 이름
            query: 업데이트할 데이터를 찾기 위한 쿼리
            data: 업서트할 데이터
            
        Returns:
            성공 여부
        """
        try:
            # 기존 데이터 검색
            existing = await self.find_one(collection, query)
            
            if existing:
                # 데이터가 존재하면 업데이트
                result = await self.update_data(collection, query, data)
                return result > 0
            else:
                # 데이터가 없으면 삽입
                result = await self.insert_data(collection, data)
                return result > 0
        except Exception as e:
            logger.error(f"데이터 업서트 중 오류 발생: {str(e)}")
            return False
            
    async def update_data(self, collection: str, query: Dict[str, Any], update_data: Dict[str, Any]) -> int:
        """지정된 쿼리로 데이터를 업데이트합니다.
        
        Args:
            collection: 업데이트할 컬렉션/테이블 이름
            query: 업데이트할 데이터를 찾기 위한 쿼리
            update_data: 업데이트할 데이터
            
        Returns:
            업데이트된 레코드 수
        """
        try:
            session = self.get_session()
            table = metadata.tables.get(collection)
            
            if not table:
                logger.error(f"테이블 {collection}이(가) 존재하지 않습니다.")
                return 0
            
            # 쿼리 구성
            stmt = table.update()
            for key, value in query.items():
                if hasattr(table.c, key):
                    stmt = stmt.where(getattr(table.c, key) == value)
            
            # 업데이트 실행
            result = session.execute(stmt.values(**update_data))
            session.commit()
            
            return result.rowcount
        except Exception as e:
            logger.error(f"데이터 업데이트 중 오류 발생: {str(e)}")
            session.rollback()
            return 0
        finally:
            session.close()
    
    async def delete_data(self, collection: str, query: Dict[str, Any]) -> int:
        """지정된 쿼리로 데이터를 삭제합니다.
        
        Args:
            collection: 삭제할 컬렉션/테이블 이름
            query: 삭제할 데이터를 찾기 위한 쿼리
            
        Returns:
            삭제된 레코드 수
        """
        try:
            session = self.get_session()
            table = metadata.tables.get(collection)
            
            if not table:
                logger.error(f"테이블 {collection}이(가) 존재하지 않습니다.")
                return 0
            
            # 쿼리 구성
            stmt = table.delete()
            for key, value in query.items():
                if hasattr(table.c, key):
                    stmt = stmt.where(getattr(table.c, key) == value)
            
            # 삭제 실행
            result = session.execute(stmt)
            session.commit()
            
            return result.rowcount
        except Exception as e:
            logger.error(f"데이터 삭제 중 오류 발생: {str(e)}")
            session.rollback()
            return 0
        finally:
            session.close()


# 데이터베이스 초기화
init_db()