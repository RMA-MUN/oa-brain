from typing import Dict, Any, List
from app.agent.base import BaseAgent
from app.core.logger_handler import logger
from app.rag.rag_service import RagService


class KnowledgeAgent(BaseAgent):
    """
    知识库Agent，负责处理RAG相关任务
    """
    
    def __init__(self):
        super().__init__("knowledge_agent")
        self.rag_service = RagService()
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入数据，执行知识库查询"""
        try:
            query = input_data.get("query", "")
            
            if not query:
                return {
                    "success": False,
                    "error": "查询内容不能为空"
                }
            
            # 执行RAG查询
            result = await self.rag_service.rag_summary(query)
            
            logger.info(f"【知识库查询】成功执行查询，结果长度: {len(result)}")
            
            return {
                "success": True,
                "knowledge_content": result,
                "query": query
            }
            
        except Exception as e:
            logger.error(f"【知识库查询】失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def can_handle(self, task_type: str) -> bool:
        """判断是否能够处理特定类型的任务"""
        knowledge_task_types = [
            "knowledge_query",
            "rag_query",
            "information_retrieval",
            "document_search",
            "knowledge_base"
        ]
        return task_type in knowledge_task_types
    
    async def search_documents(self, query: str, user_id: str = None) -> Dict[str, Any]:
        """搜索文档"""
        try:
            # 这里可以扩展为更复杂的文档搜索逻辑
            result = await self.rag_service.rag_summary(query)
            
            return {
                "success": True,
                "documents": [result],
                "query": query
            }
            
        except Exception as e:
            logger.error(f"【文档搜索】失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_relevant_knowledge(self, topic: str) -> Dict[str, Any]:
        """获取特定主题的相关知识"""
        try:
            query = f"关于{topic}的详细信息"
            result = await self.rag_service.rag_summary(query)
            
            return {
                "success": True,
                "topic": topic,
                "knowledge": result
            }
            
        except Exception as e:
            logger.error(f"【知识获取】失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }