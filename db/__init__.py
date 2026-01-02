from db.connect.connect_cosmosdb import CosmosDBClient
from api.core.exceptions import AgentProcessingError
from api.core.logger import APILogger

# Lazy initialization - 실제 사용 시점에 초기화
_cosmos_db_client = None
_prompt_container = None
_chat_history_container = None
_session_container = None
_customer_info_container = None
logger = APILogger()


def _init_cosmos_client():
    """CosmosDB 클라이언트를 초기화합니다."""
    global _cosmos_db_client
    if _cosmos_db_client is None:
        _cosmos_db_client = CosmosDBClient()
    return _cosmos_db_client


# Property-like access for backward compatibility
class _LazyContainer:
    def __init__(self, db_name, container_name, partition_key):
        self.db_name = db_name
        self.container_name = container_name
        self.partition_key = partition_key
        self._container = None

    def __getattr__(self, name):
        if self._container is None:
            try:
                client = _init_cosmos_client()
                self._container = client.get_container(
                    database_name=self.db_name,
                    container_name=self.container_name,
                    partition_key_path=self.partition_key,
                )
            except AgentProcessingError as e:
                # 로깅 후 재발생 - 이렇게 하면 첫 API 호출 시 명확한 에러 메시지
                logger.error(
                    f"CosmosDB 컨테이너 초기화 실패 ({self.container_name}): {e}"
                )
                raise
        return getattr(self._container, name)


# 기존 코드와의 호환성 유지
cosmos_db_client = None  # 직접 접근 시 초기화 필요

prompt_container = _LazyContainer(
    db_name="meritz_pt_db", container_name="meritz_pt_db", partition_key="/prompt_type"
)

chat_history_container = _LazyContainer(
    db_name="meritz_chat_history_db",
    container_name="meritz_chat_history",
    partition_key="/userId",
)

session_container = _LazyContainer(
    db_name="sessions_db", container_name="sessions", partition_key="/user_no"
)

customer_info_container = _LazyContainer(
    db_name="customer_info_db", container_name="customer_info", partition_key="/room_id"
)
