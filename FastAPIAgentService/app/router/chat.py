from typing import List
import uuid

from fastapi.routing import APIRouter
from fastapi import UploadFile, File, Depends
from fastapi.responses import StreamingResponse

from app.agent.agent import get_agent_stream_response, get_main_agent_stream_response, get_main_agent_response
from app.router.chat_service import ChatService, get_router_service

from app.schemas.rag_schemas import QueryRequest, RAGResponse, RAGRequest, SessionResponse, ReorderResponse, ReorderRequest, ParamExtractionRequest, ParamExtractionResponse
from app.agent.main_agent import MainAgent
from app.utils.auth_utils import get_current_user_id
from app.core.success_response import success_response
from app.core.rate_limit import rate_limit


chat_router = APIRouter(prefix="/api", tags=["api"])

@chat_router.post("/agent/query/stream")
async def query_stream(
        request: QueryRequest,
        user_id: str = Depends(get_current_user_id),
        _: None = Depends(rate_limit(limit=10, window=60))
):
    """查询Agent流式响应"""
    # 如果没有提供session_id，自动生成一个
    session_id = request.session_id or str(uuid.uuid4())
    
    # 直接调用get_agent_stream_response函数
    return StreamingResponse(
        get_agent_stream_response(request.query, session_id, user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@chat_router.post("/main-agent/query/stream")
async def main_agent_query_stream(
        request: QueryRequest,
        user_id: str = Depends(get_current_user_id),
        _: None = Depends(rate_limit(limit=10, window=60))
):
    """查询主Agent流式响应（协调多个子Agent）"""
    # 如果没有提供session_id，自动生成一个
    session_id = request.session_id or str(uuid.uuid4())
    
    # 调用主Agent流式响应函数
    return StreamingResponse(
        get_main_agent_stream_response(request.query, session_id, user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

@chat_router.post("/main-agent/query")
async def main_agent_query(request: QueryRequest, user_id: str = Depends(get_current_user_id), router_service: ChatService = Depends(get_router_service)):
    """查询主Agent, 非流式响应"""
    response = await get_main_agent_response(request.query, request.session_id, user_id)
    return success_response(data=response)

@chat_router.post("/rag/query")
async def query_rag(
        request: RAGRequest,
        router_service: ChatService = Depends(get_router_service),
        _: None = Depends(rate_limit(limit=15, window=60))
):
    """RAG检索"""
    response = await router_service.handle_rag_query(request.query)
    return success_response(data=RAGResponse(response=response))


@chat_router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, user_id: str = Depends(get_current_user_id), router_service: ChatService = Depends(get_router_service)):
    """获取会话信息，使用user_id验证"""
    history = await router_service.handle_get_session(session_id, user_id)
    return success_response(data=SessionResponse(session_id=session_id, history=history))



@chat_router.delete("/session/{session_id}")
async def delete_session(session_id: str, user_id: str = Depends(get_current_user_id), router_service: ChatService = Depends(get_router_service)):
    """删除会话"""
    await router_service.handle_delete_session(session_id, user_id)
    return success_response(message=f"Session {session_id} deleted successfully")

@chat_router.get("/sessions")
async def get_all_sessions(router_service: ChatService = Depends(get_router_service)):
    """获取所有会话ID"""
    session_ids = await router_service.handle_get_all_sessions()
    return success_response(data={"sessions": session_ids})



@chat_router.get("/sessions/{user_id}")
async def get_user_sessions(user_id: str, current_user_id: str = Depends(get_current_user_id), router_service: ChatService = Depends(get_router_service)):
    """获取用户所有会话ID"""
    session_ids = await router_service.handle_get_user_sessions(user_id, current_user_id)
    return success_response(data={"sessions": session_ids})


@chat_router.post("/vector/add/single")
async def add_vector_single(
        file: UploadFile = File(...),
        user_id: str = Depends(get_current_user_id),
        router_service: ChatService = Depends(get_router_service),
        _: None = Depends(rate_limit(limit=5, window=60))
):
    """上传文件，将文件保存到向量数据库，仅支持TXT和PDF"""
    filename = await router_service.handle_add_vector_single(file, user_id)
    return success_response(message=f"文件 {filename} 已成功上传并存储到向量数据库")



@chat_router.post("/vector/add/multiple")
async def add_vector_multiple(
        files: List[UploadFile] = File(..., description="要上传的文件列表，仅支持PDF和TXT格式"),
        user_id: str = Depends(get_current_user_id),
        router_service: ChatService = Depends(get_router_service),
        _: None = Depends(rate_limit(limit=3, window=60))
):
    """上传多个文件，将文件保存到向量数据库，仅支持TXT和PDF"""
    filenames = await router_service.handle_add_vector_multiple(files, user_id)
    return success_response(message=f"文件 {filenames} 已成功上传并存储到向量数据库")


@chat_router.delete("/vector/clean")
async def clean_user_vectors(user_id: str = Depends(get_current_user_id), router_service: ChatService = Depends(get_router_service)):
    """删除用户上传的所有向量"""
    await router_service.clean_user_upload(user_id)
    return success_response(message="已成功删除用户上传的所有向量")


@chat_router.post("/reorder", response_model=ReorderResponse)
async def reorder_documents(
        request: ReorderRequest,
        router_service: ChatService = Depends(get_router_service),
        _: None = Depends(rate_limit(limit=20, window=60))
):
    """使用Ollama本地的嵌入模型对文档进行中文重排序"""
    sorted_docs = await router_service.handle_reorder(request.query, request.documents)
    return success_response(data=ReorderResponse(documents=sorted_docs))


@chat_router.post("/test/param-extraction", response_model=ParamExtractionResponse)
async def test_param_extraction(
        request: ParamExtractionRequest,
        user_id: str = Depends(get_current_user_id),
        _: None = Depends(rate_limit(limit=10, window=60))
):
    """测试参数提取功能"""
    try:
        # 创建MainAgent实例
        main_agent = MainAgent()
        
        # 构建测试子任务
        subtask = {
            "task_type": "test_param_extraction",
            "description": f"测试参数提取: {request.user_input}",
            "required_params": request.required_params,
            "params": {}
        }
        
        # 构建测试状态
        from app.agent.base import AgentState
        state = AgentState()
        state.user_input = request.user_input
        state.session_id = "test_session"
        state.user_id = user_id
        
        # 执行参数提取
        await main_agent._check_params_complete(subtask, state)
        
        # 获取提取的参数和缺失的参数
        extracted_params = subtask.get("params", {})
        missing_params = [
            p for p in request.required_params 
            if p not in extracted_params or not str(extracted_params.get(p, "")).strip()
        ]
        
        # 构建响应
        status = "success" if not missing_params else "partial"
        response = ParamExtractionResponse(
            extracted_params=extracted_params,
            missing_params=missing_params,
            status=status
        )
        
        return success_response(data=response)
    except Exception as e:
        # 构建错误响应
        response = ParamExtractionResponse(
            extracted_params={},
            missing_params=request.required_params,
            status=f"error: {str(e)}"
        )
        return success_response(data=response)