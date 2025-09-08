from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.services.llm import LLMService

class VectorDBService:
    """벡터 데이터베이스 서비스
    
    텍스트 임베딩을 저장하고 유사도 검색을 수행합니다.
    """
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        # 기본 컬렉션 이름 설정 (설정에 없는 경우 기본값 사용)
        self.collection_name = getattr(settings, "VECTOR_DB_COLLECTION", "documents")
        self.llm_service = llm_service or LLMService()
        self.initialized = False
        self.client = None
        
    async def initialize(self):
        """벡터 데이터베이스 초기화"""
        if self.initialized:
            return
            
        try:
            # 벡터 DB 클라이언트 초기화 (사용하는 벡터 DB에 따라 구현)
            vector_db_type = getattr(settings, "VECTOR_DB_TYPE", "chroma").lower()
            
            if vector_db_type == "qdrant":
                await self._init_qdrant()
            elif vector_db_type == "pinecone":
                await self._init_pinecone()
            elif vector_db_type == "weaviate":
                await self._init_weaviate()
            else:
                # 기본값으로 ChromaDB 사용
                await self._init_chroma()
                
            self.initialized = True
            logger.info(f"Vector database initialized: {settings.VECTOR_DB_TYPE}")
            
        except Exception as e:
            logger.error(f"Vector database initialization failed: {str(e)}")
            raise
    
    async def _init_qdrant(self):
        """Qdrant 벡터 DB 초기화"""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models
            
            # Qdrant 클라이언트 생성
            self.client = QdrantClient(
                url=settings.VECTOR_DB_URL,
                api_key=settings.VECTOR_DB_API_KEY
            )
            
            # 컬렉션 존재 여부 확인 및 생성
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            if self.collection_name not in collection_names:
                # 컬렉션 생성
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=settings.EMBEDDING_DIMENSION,
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Created new Qdrant collection: {self.collection_name}")
            
        except ImportError:
            logger.error("Qdrant client not installed. Please install with 'pip install qdrant-client'")
            raise
        except Exception as e:
            logger.error(f"Qdrant initialization failed: {str(e)}")
            raise
    
    async def _init_pinecone(self):
        """Pinecone 벡터 DB 초기화"""
        try:
            import pinecone
            
            # Pinecone 초기화
            pinecone.init(
                api_key=settings.VECTOR_DB_API_KEY,
                environment=settings.VECTOR_DB_ENVIRONMENT
            )
            
            # 인덱스 존재 여부 확인 및 생성
            if self.collection_name not in pinecone.list_indexes():
                # 인덱스 생성
                pinecone.create_index(
                    name=self.collection_name,
                    dimension=settings.EMBEDDING_DIMENSION,
                    metric="cosine"
                )
                logger.info(f"Created new Pinecone index: {self.collection_name}")
            
            # 인덱스 연결
            self.client = pinecone.Index(self.collection_name)
            
        except ImportError:
            logger.error("Pinecone client not installed. Please install with 'pip install pinecone-client'")
            raise
        except Exception as e:
            logger.error(f"Pinecone initialization failed: {str(e)}")
            raise
    
    async def _init_weaviate(self):
        """Weaviate 벡터 DB 초기화"""
        try:
            import weaviate
            from weaviate.auth import AuthApiKey
            
            # Weaviate 클라이언트 생성
            auth_config = AuthApiKey(api_key=settings.VECTOR_DB_API_KEY)
            self.client = weaviate.Client(
                url=settings.VECTOR_DB_URL,
                auth_client_secret=auth_config
            )
            
            # 클래스 존재 여부 확인 및 생성
            if not self.client.schema.exists(self.collection_name):
                # 클래스 생성
                class_obj = {
                    "class": self.collection_name,
                    "vectorizer": "none",  # 외부 임베딩 사용
                    "properties": [
                        {"name": "content", "dataType": ["text"]},
                        {"name": "metadata", "dataType": ["object"]}
                    ]
                }
                self.client.schema.create_class(class_obj)
                logger.info(f"Created new Weaviate class: {self.collection_name}")
            
        except ImportError:
            logger.error("Weaviate client not installed. Please install with 'pip install weaviate-client'")
            raise
        except Exception as e:
            logger.error(f"Weaviate initialization failed: {str(e)}")
            raise
    
    async def _init_inmemory(self):
        """인메모리 벡터 DB 초기화"""
        # 간단한 인메모리 벡터 저장소 구현
        self.client = {
            "vectors": [],
            "metadata": []
        }
        logger.info("Initialized in-memory vector database")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def store_embeddings(self, texts: List[str], metadata: List[Dict[str, Any]]) -> List[str]:
        """텍스트 임베딩 저장
        
        Args:
            texts: 임베딩할 텍스트 목록
            metadata: 각 텍스트에 대한 메타데이터 목록
            
        Returns:
            저장된 문서 ID 목록
        """
        if not self.initialized:
            await self.initialize()
            
        try:
            # 텍스트 임베딩 생성
            embeddings = []
            for text in texts:
                embedding = await self.llm_service.generate_embeddings(text)
                embeddings.append(embedding)
            
            # 벡터 DB에 저장 (사용하는 벡터 DB에 따라 구현)
            if settings.VECTOR_DB_TYPE.lower() == "qdrant":
                return await self._store_qdrant(texts, embeddings, metadata)
            elif settings.VECTOR_DB_TYPE.lower() == "pinecone":
                return await self._store_pinecone(texts, embeddings, metadata)
            elif settings.VECTOR_DB_TYPE.lower() == "weaviate":
                return await self._store_weaviate(texts, embeddings, metadata)
            else:
                # 기본값: 인메모리 벡터 DB
                return await self._store_inmemory(texts, embeddings, metadata)
                
        except Exception as e:
            logger.error(f"Storing embeddings failed: {str(e)}")
            raise
    
    async def _store_qdrant(self, texts: List[str], embeddings: List[List[float]], metadata: List[Dict[str, Any]]) -> List[str]:
        """Qdrant에 임베딩 저장"""
        from qdrant_client.http import models
        
        # 문서 ID 생성
        import uuid
        ids = [str(uuid.uuid4()) for _ in range(len(texts))]
        
        # 포인트 생성
        points = [
            models.PointStruct(
                id=id,
                vector=embedding,
                payload={
                    "text": text,
                    **meta
                }
            )
            for id, text, embedding, meta in zip(ids, texts, embeddings, metadata)
        ]
        
        # 포인트 업로드
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        return ids
    
    async def _store_pinecone(self, texts: List[str], embeddings: List[List[float]], metadata: List[Dict[str, Any]]) -> List[str]:
        """Pinecone에 임베딩 저장"""
        # 문서 ID 생성
        import uuid
        ids = [str(uuid.uuid4()) for _ in range(len(texts))]
        
        # 벡터 생성
        vectors = [
            (id, embedding, {"text": text, **meta})
            for id, text, embedding, meta in zip(ids, texts, embeddings, metadata)
        ]
        
        # 벡터 업로드
        self.client.upsert(vectors=vectors)
        
        return ids
    
    async def _store_weaviate(self, texts: List[str], embeddings: List[List[float]], metadata: List[Dict[str, Any]]) -> List[str]:
        """Weaviate에 임베딩 저장"""
        # 문서 ID 생성
        import uuid
        ids = []
        
        # 객체 생성 및 업로드
        with self.client.batch as batch:
            for text, embedding, meta in zip(texts, embeddings, metadata):
                id = str(uuid.uuid4())
                batch.add_data_object(
                    data_object={
                        "content": text,
                        "metadata": meta
                    },
                    class_name=self.collection_name,
                    uuid=id,
                    vector=embedding
                )
                ids.append(id)
        
        return ids
    
    async def _store_inmemory(self, texts: List[str], embeddings: List[List[float]], metadata: List[Dict[str, Any]]) -> List[str]:
        """인메모리 벡터 DB에 임베딩 저장"""
        # 문서 ID 생성
        import uuid
        ids = [str(uuid.uuid4()) for _ in range(len(texts))]
        
        # 벡터 및 메타데이터 저장
        for id, text, embedding, meta in zip(ids, texts, embeddings, metadata):
            self.client["vectors"].append({
                "id": id,
                "vector": embedding
            })
            self.client["metadata"].append({
                "id": id,
                "text": text,
                **meta
            })
        
        return ids
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def search_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """유사 문서 검색
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수
            
        Returns:
            유사 문서 목록 (텍스트, 메타데이터, 유사도 포함)
        """
        if not self.initialized:
            await self.initialize()
            
        try:
            # 쿼리 임베딩 생성
            query_embedding = await self.llm_service.generate_embeddings(query)
            
            # 유사 문서 검색 (사용하는 벡터 DB에 따라 구현)
            if settings.VECTOR_DB_TYPE.lower() == "qdrant":
                return await self._search_qdrant(query_embedding, top_k)
            elif settings.VECTOR_DB_TYPE.lower() == "pinecone":
                return await self._search_pinecone(query_embedding, top_k)
            elif settings.VECTOR_DB_TYPE.lower() == "weaviate":
                return await self._search_weaviate(query_embedding, top_k)
            else:
                # 기본값: 인메모리 벡터 DB
                return await self._search_inmemory(query_embedding, top_k)
                
        except Exception as e:
            logger.error(f"Similarity search failed: {str(e)}")
            raise
    
    async def _search_qdrant(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """Qdrant에서 유사 문서 검색"""
        # 검색 수행
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k
        )
        
        # 결과 변환
        results = []
        for result in search_result:
            results.append({
                "id": result.id,
                "text": result.payload.get("text", ""),
                "metadata": {k: v for k, v in result.payload.items() if k != "text"},
                "similarity": result.score
            })
        
        return results
    
    async def _search_pinecone(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """Pinecone에서 유사 문서 검색"""
        # 검색 수행
        search_result = self.client.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        # 결과 변환
        results = []
        for match in search_result["matches"]:
            results.append({
                "id": match["id"],
                "text": match["metadata"].get("text", ""),
                "metadata": {k: v for k, v in match["metadata"].items() if k != "text"},
                "similarity": match["score"]
            })
        
        return results
    
    async def _search_weaviate(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """Weaviate에서 유사 문서 검색"""
        # 검색 수행
        search_result = (
            self.client.query
            .get(self.collection_name, ["content", "metadata"])
            .with_near_vector({"vector": query_embedding})
            .with_limit(top_k)
            .do()
        )
        
        # 결과 변환
        results = []
        for obj in search_result["data"]["Get"][self.collection_name]:
            results.append({
                "id": obj["_additional"]["id"],
                "text": obj["content"],
                "metadata": obj["metadata"],
                "similarity": obj["_additional"]["certainty"]
            })
        
        return results
    
    async def _search_inmemory(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """인메모리 벡터 DB에서 유사 문서 검색"""
        import numpy as np
        
        # 코사인 유사도 계산
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        # 모든 벡터와의 유사도 계산
        similarities = []
        for i, item in enumerate(self.client["vectors"]):
            similarity = cosine_similarity(query_embedding, item["vector"])
            similarities.append((i, similarity))
        
        # 유사도 기준 정렬 및 상위 k개 선택
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_indices = [idx for idx, _ in similarities[:top_k]]
        
        # 결과 변환
        results = []
        for idx in top_indices:
            vector_item = self.client["vectors"][idx]
            metadata_item = self.client["metadata"][idx]
            results.append({
                "id": metadata_item["id"],
                "text": metadata_item["text"],
                "metadata": {k: v for k, v in metadata_item.items() if k not in ["id", "text"]},
                "similarity": similarities[idx][1]
            })
        
        return results
    
    async def delete_by_ids(self, ids: List[str]) -> bool:
        """ID로 문서 삭제
        
        Args:
            ids: 삭제할 문서 ID 목록
            
        Returns:
            성공 여부
        """
        if not self.initialized:
            await self.initialize()
            
        try:
            # 문서 삭제 (사용하는 벡터 DB에 따라 구현)
            if settings.VECTOR_DB_TYPE.lower() == "qdrant":
                return await self._delete_qdrant(ids)
            elif settings.VECTOR_DB_TYPE.lower() == "pinecone":
                return await self._delete_pinecone(ids)
            elif settings.VECTOR_DB_TYPE.lower() == "weaviate":
                return await self._delete_weaviate(ids)
            else:
                # 기본값: 인메모리 벡터 DB
                return await self._delete_inmemory(ids)
                
        except Exception as e:
            logger.error(f"Deleting documents failed: {str(e)}")
            raise
    
    async def _delete_qdrant(self, ids: List[str]) -> bool:
        """Qdrant에서 문서 삭제"""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=ids
        )
        return True
    
    async def _delete_pinecone(self, ids: List[str]) -> bool:
        """Pinecone에서 문서 삭제"""
        self.client.delete(ids=ids)
        return True
    
    async def _delete_weaviate(self, ids: List[str]) -> bool:
        """Weaviate에서 문서 삭제"""
        for id in ids:
            self.client.data_object.delete(id, self.collection_name)
        return True
    
    async def _delete_inmemory(self, ids: List[str]) -> bool:
        """인메모리 벡터 DB에서 문서 삭제"""
        # ID로 인덱스 찾기
        indices_to_remove = []
        for i, item in enumerate(self.client["metadata"]):
            if item["id"] in ids:
                indices_to_remove.append(i)
        
        # 역순으로 삭제 (인덱스 변화 방지)
        for idx in sorted(indices_to_remove, reverse=True):
            del self.client["vectors"][idx]
            del self.client["metadata"][idx]
        
        return True
    
    async def close(self):
        """클라이언트 종료"""
        if settings.VECTOR_DB_TYPE.lower() == "qdrant":
            if hasattr(self.client, "close"):
                await self.client.close()
        elif settings.VECTOR_DB_TYPE.lower() == "pinecone":
            # Pinecone은 명시적 종료 필요 없음
            pass
        elif settings.VECTOR_DB_TYPE.lower() == "weaviate":
            if hasattr(self.client, "close"):
                self.client.close()
        
        # LLM 서비스 종료
        await self.llm_service.close()