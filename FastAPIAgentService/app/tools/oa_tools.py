"""
智能体可以调用的工具，负责处理OA相关的任务
"""
import os
import json
import httpx

from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from langchain_core.tools import tool

from app.core.logger_handler import logger
from app.schemas.oa_schemas import (
    AttendanceCreateRequest,
    AttendanceUpdateRequest,
    InformCreateRequest,
    InformUpdateRequest,
)

# 确保请求数据为严格JSON格式
def ensure_strict_json(data):
    """确保数据为严格JSON格式"""

    return json.loads(json.dumps(data))

load_dotenv()

# Django API基础URL
DJANGO_API_BASE_URL = os.getenv("DJANGO_API_URL")


# 考勤相关工具
@tool(description="获取考勤类型列表，不需要参数")
async def get_attendance_types() -> str:
    """获取考勤类型列表工具"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{DJANGO_API_BASE_URL}/Attendance/attendance-type/")
            response.raise_for_status()
            data = response.json()
            
            # 验证数据格式
            if not isinstance(data, list):
                return f"获取考勤类型失败: 返回数据格式错误，期望列表但得到 {type(data).__name__}"
            
            if not data:
                return "暂无考勤类型"
                
            return f"考勤类型列表：\n" + "\n".join([f"- {item['name']} (ID: {item['id']})" for item in data if isinstance(item, dict) and 'name' in item and 'id' in item])
    except Exception as e:
        logger.error(f"获取考勤类型失败: {str(e)}")
        return f"获取考勤类型失败: {str(e)}"


@tool(description="获取当前用户的考勤审批人信息，需要提供JWT token作为参数")
async def get_attendance_responser(token: str) -> str:
    """获取考勤审批人信息工具"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{DJANGO_API_BASE_URL}/Attendance/attendance-responser/",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            data = response.json()
            
            # 验证数据格式
            if not isinstance(data, dict):
                return f"获取考勤审批人失败: 返回数据格式错误，期望对象但得到 {type(data).__name__}"
                
            if 'username' not in data or 'email' not in data:
                return "获取考勤审批人失败: 返回数据缺少必要字段"
                
            return f"考勤审批人信息：\n- 用户名: {data['username']}\n- 邮箱: {data['email']}"
    except Exception as e:
        logger.error(f"获取考勤审批人失败: {str(e)}")
        return f"获取考勤审批人失败: {str(e)}"


@tool(description="获取考勤记录列表，需要提供JWT token和查询范围参数who（可选值：requester, responser, leader, manager）")
async def get_attendance_records(token: str, who: Optional[str] = None) -> str:
    """获取考勤记录列表工具"""
    try:
        params = {}
        if who:
            params["who"] = who
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{DJANGO_API_BASE_URL}/Attendance/attendance/",
                headers={"Authorization": f"Bearer {token}"},
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            # 验证数据格式，处理可能的dict格式（如分页响应）
            if isinstance(data, dict):
                # 检查是否是分页响应格式
                if 'results' in data and isinstance(data['results'], list):
                    data = data['results']
                else:
                    return f"获取考勤记录失败: 返回数据格式错误，期望列表或包含results字段的对象，但得到 {type(data).__name__}"
            elif not isinstance(data, list):
                return f"获取考勤记录失败: 返回数据格式错误，期望列表但得到 {type(data).__name__}"
            
            if not data:
                return "暂无考勤记录"
                
            result = "考勤记录列表：\n"
            for record in data:
                # 验证每条记录的格式
                if not isinstance(record, dict):
                    continue
                if 'id' not in record or 'type' not in record or 'status' not in record:
                    continue
                result += f"- ID: {record['id']}, 类型: {record['type']}, 状态: {record['status']}\n"
                if 'start_time' in record and 'end_time' in record:
                    result += f"  时间: {record['start_time']} 至 {record['end_time']}\n"
                if record.get('reason'):
                    result += f"  原因: {record['reason']}\n"
            return result
    except Exception as e:
        logger.error(f"获取考勤记录失败: {str(e)}")
        return f"获取考勤记录失败: {str(e)}"


@tool(description="创建考勤记录，必须提供以下参数：1) JWT token (字符串)，2) title (字符串，考勤标题)，3) attendance_type_id (整数，考勤类型ID)，4) start_time (字符串，开始时间，格式：2024-01-01 09:00:00)，5) end_time (字符串，结束时间，格式：2024-01-02 18:00:00)，6) request_content (字符串，请假原因)。")
async def create_attendance_record(
    token: str,
    request_body: AttendanceCreateRequest
) -> str:
    """创建考勤记录工具"""
    try:
        # 从 Pydantic 模型中提取参数
        title = request_body.title
        attendance_type_id = request_body.attendance_type_id
        start_time = request_body.start_time
        end_time = request_body.end_time
        request_content = request_body.request_content

        # 确保时间格式正确
        try:
            # 检查时间格式是否为 "YYYY-MM-DD HH:MM:SS"
            datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return "创建考勤记录失败：时间格式错误，正确格式为：YYYY-MM-DD HH:MM:SS"

        # 构建请求数据（直接使用 Pydantic 模型的字典形式）
        request_data = request_body.dict()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DJANGO_API_BASE_URL}/Attendance/attendance/",
                headers={"Authorization": f"Bearer {token}"},
                json=request_data
            )
            if response.status_code >= 400:
                try:
                    error_body = response.json()
                except ValueError:
                    error_body = response.text
                logger.error(
                    f"创建考勤记录失败: status={response.status_code}, request_data={request_data}, response={error_body}"
                )
                return f"创建考勤记录失败（{response.status_code}）：{error_body}"

            response.raise_for_status()
            data = response.json()
            
            # 从返回数据中提取详细信息
            record_id = data.get('id', '未知')
            record_title = data.get('title', '未知')
            
            # 获取考勤类型信息
            attendance_type = data.get('attendance_type', {})
            type_name = attendance_type.get('name', '未知')
            
            # 获取申请人信息
            requester_name = data.get('requester_name', '未知')
            requester_email = data.get('requester', {}).get('email', '未知')
            
            # 获取审批人信息
            responser_name = data.get('responser_name', '未知')
            
            # 获取状态（1=审批中，2=已审批，3=已拒绝）
            status_code = data.get('status', 0)
            status_map = {1: '审批中', 2: '已审批', 3: '已拒绝'}
            record_status = status_map.get(status_code, f'未知状态({status_code})')
            
            # 获取时间信息
            start_time = data.get('start_time', '未知')
            end_time = data.get('end_time', '未知')
            request_content = data.get('request_content', '未知')
            
            # 格式化返回信息
            result = f"考勤记录创建成功！\n"
            result += f"┌───────────────────────────────\n"
            result += f"│ 申请标题：{record_title}\n"
            result += f"│ 记录ID：{record_id}\n"
            result += f"│ 考勤类型：{type_name}\n"
            result += f"│ 申请人：{requester_name} ({requester_email})\n"
            result += f"│ 审批人：{responser_name}\n"
            result += f"│ 请假原因：{request_content}\n"
            result += f"│ 请假时间：{start_time} 至 {end_time}\n"
            result += f"│ 当前状态：{record_status}\n"
            result += f"└───────────────────────────────"
            
            return result
    except Exception as e:
        logger.error(f"创建考勤记录失败: {str(e)}")
        return f"创建考勤记录失败: {str(e)}"


@tool(description="更新考勤记录状态，需要提供JWT token、记录ID和更新信息（status, comment）")
async def update_attendance_record(
    token: str,
    record_id: int,
    status: str = None,
    comment: str = None,
    update_data: AttendanceUpdateRequest = None
) -> str:
    """更新考勤记录状态工具"""
    try:
        # 优先使用单独的参数，如果没有则使用update_data
        if status is None and update_data:
            status = update_data.status
        if comment is None and update_data:
            comment = update_data.comment
        
        # 验证必需参数
        if status is None:
            return "更新考勤记录失败：缺少必需参数status"
        
        # 验证status值
        if status not in ["approved", "rejected"]:
            return "更新考勤记录失败：status值必须为approved或rejected"
        
        request_data = {
            "status": status
        }
        if comment:
            request_data["comment"] = comment
        
        # 确保请求数据为严格JSON格式
        request_data = ensure_strict_json(request_data)
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{DJANGO_API_BASE_URL}/Attendance/attendance/",
                headers={"Authorization": f"Bearer {token}"},
                json=request_data
            )
            response.raise_for_status()
            data = response.json()
            return f"考勤记录更新成功！\nID: {data['id']}\n状态: {data['status']}"
    except Exception as e:
        logger.error(f"更新考勤记录失败: {str(e)}")
        return f"更新考勤记录失败: {str(e)}"


@tool(description="获取部门列表，需要提供JWT token")
async def get_departments(token: str) -> str:
    """获取部门列表工具"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{DJANGO_API_BASE_URL}/staff/department/",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            data = response.json()
            
            # 验证数据格式
            if not isinstance(data, list):
                return f"获取部门列表失败: 返回数据格式错误，期望列表但得到 {type(data).__name__}"
            
            if not data:
                return "暂无部门信息"
                
            result = "部门列表：\n"
            for dept in data:
                if not isinstance(dept, dict):
                    continue
                if 'name' not in dept or 'leader' not in dept or 'members' not in dept:
                    continue
                result += f"- 部门名称: {dept['name']}\n"
                result += f"  负责人: {dept['leader']}\n"
                result += f"  成员: {', '.join(dept['members'])}\n"
            return result
    except Exception as e:
        logger.error(f"获取部门列表失败: {str(e)}")
        return f"获取部门列表失败: {str(e)}"


@tool(description="获取用户列表（按部门分组），需要提供JWT token")
async def get_users(token: str) -> str:
    """获取用户列表工具"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{DJANGO_API_BASE_URL}/staff/user/",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            data = response.json()
            
            # 验证数据格式
            if not isinstance(data, dict):
                return f"获取用户列表失败: 返回数据格式错误，期望对象但得到 {type(data).__name__}"
            
            if not data:
                return "暂无用户信息"
                
            result = "用户列表（按部门分组）：\n"
            for dept_name, dept_data in data.items():
                if not isinstance(dept_data, dict):
                    continue
                result += f"\n【{dept_name}】\n"
                if dept_data.get("leader") and isinstance(dept_data["leader"], list):
                    result += "负责人：\n"
                    for leader in dept_data["leader"]:
                        if isinstance(leader, dict) and 'username' in leader and 'email' in leader:
                            result += f"- {leader['username']} ({leader['email']})\n"
                if dept_data.get("members") and isinstance(dept_data["members"], list):
                    result += "成员：\n"
                    for member in dept_data["members"]:
                        if isinstance(member, dict) and 'username' in member and 'email' in member:
                            result += f"- {member['username']} ({member['email']})\n"
            return result
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        return f"获取用户列表失败: {str(e)}"


@tool(description="获取通知列表，需要提供JWT token，可选参数page和page_size用于分页")
async def get_informs(token: str, page: int = 1, page_size: int = 10) -> str:
    """获取通知列表工具"""
    try:
        params = {"page": page, "page_size": page_size}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{DJANGO_API_BASE_URL}/inform/inform/",
                headers={"Authorization": f"Bearer {token}"},
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            # 验证数据格式
            if isinstance(data, dict):
                # 检查是否是分页响应格式
                if 'results' in data and isinstance(data['results'], list):
                    results = data['results']
                    count = data.get('count', 0)
                else:
                    return f"获取通知列表失败: 返回数据格式错误，期望包含results字段的对象，但得到 {type(data).__name__}"
            elif isinstance(data, list):
                # 直接返回列表格式
                results = data
                count = len(data)
            else:
                return f"获取通知列表失败: 返回数据格式错误，期望对象或列表但得到 {type(data).__name__}"
                
            if not results:
                return f"通知列表（第{page}页）：暂无通知"
                
            result = f"通知列表（第{page}页，共{count}条）：\n"
            for inform in results:
                if not isinstance(inform, dict):
                    continue
                if 'title' not in inform or 'content' not in inform or 'create_time' not in inform:
                    continue
                result += f"- 标题: {inform['title']}\n"
                result += f"  内容: {inform['content'][:100]}..." if len(inform['content']) > 100 else f"  内容: {inform['content']}\n"
                result += f"  创建时间: {inform['create_time']}\n"
            return result
    except Exception as e:
        logger.error(f"获取通知列表失败: {str(e)}")
        return f"获取通知列表失败: {str(e)}"


@tool(description="创建通知，需要提供JWT token和通知信息（title, content, public, department_ids）")
async def create_inform(
    token: str,
    title: str = None,
    content: str = None,
    public: bool = False,
    department_ids: list = None,
    inform_data: InformCreateRequest = None
) -> str:
    """创建通知工具"""
    try:
        # 优先使用单独的参数，如果没有则使用inform_data
        if title is None and inform_data:
            title = inform_data.title
        if content is None and inform_data:
            content = inform_data.content
        if inform_data:
            public = inform_data.public
            department_ids = inform_data.department_ids
        
        # 验证必需参数
        if title is None or content is None:
            return "创建通知失败：缺少必需参数title或content"
        
        request_data = {
            "title": title,
            "content": content,
            "public": public
        }
        if department_ids:
            request_data["department_ids"] = department_ids
        
        # 确保请求数据为严格JSON格式
        request_data = ensure_strict_json(request_data)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DJANGO_API_BASE_URL}/inform/inform/",
                headers={"Authorization": f"Bearer {token}"},
                json=request_data
            )
            response.raise_for_status()
            data = response.json()
            return f"通知创建成功！\nID: {data['id']}\n标题: {data['title']}"
    except Exception as e:
        logger.error(f"创建通知失败: {str(e)}")
        return f"创建通知失败: {str(e)}"


@tool(description="更新通知，需要提供JWT token、通知ID和更新信息（title, content, public, department_ids）")
async def update_inform(
    token: str,
    inform_id: int,
    title: str = None,
    content: str = None,
    public: bool = None,
    department_ids: list = None,
    update_data: InformUpdateRequest = None
) -> str:
    """更新通知工具"""
    try:
        # 优先使用单独的参数，如果没有则使用update_data
        if title is None and update_data:
            title = update_data.title
        if content is None and update_data:
            content = update_data.content
        if public is None and update_data:
            public = update_data.public
        if department_ids is None and update_data:
            department_ids = update_data.department_ids
        
        # 构建请求数据
        request_data = {}
        if title:
            request_data["title"] = title
        if content:
            request_data["content"] = content
        if public is not None:
            request_data["public"] = public
        if department_ids:
            request_data["department_ids"] = department_ids
        
        # 确保请求数据为严格JSON格式
        request_data = ensure_strict_json(request_data)
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{DJANGO_API_BASE_URL}/inform/inform/",
                headers={"Authorization": f"Bearer {token}"},
                json=request_data
            )
            response.raise_for_status()
            data = response.json()
            return f"通知更新成功！\nID: {data['id']}\n标题: {data['title']}"
    except Exception as e:
        logger.error(f"更新通知失败: {str(e)}")
        return f"更新通知失败: {str(e)}"


@tool(description="获取最新通知（最多10条），需要提供JWT token")
async def get_latest_informs(token: str) -> str:
    """获取最新通知工具"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{DJANGO_API_BASE_URL}/home/latest/inform/",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            data = response.json()
            
            # 验证数据格式
            if not isinstance(data, list):
                return f"获取最新通知失败: 返回数据格式错误，期望列表但得到 {type(data).__name__}"
            
            if not data:
                return "暂无最新通知"
                
            result = "最新通知：\n"
            for inform in data:
                if not isinstance(inform, dict):
                    continue
                if 'title' not in inform or 'content' not in inform or 'create_time' not in inform:
                    continue
                result += f"- 标题: {inform['title']}\n"
                result += f"  内容: {inform['content'][:100]}..." if len(inform['content']) > 100 else f"  内容: {inform['content']}\n"
                result += f"  创建时间: {inform['create_time']}\n"
            return result
    except Exception as e:
        logger.error(f"获取最新通知失败: {str(e)}")
        return f"获取最新通知失败: {str(e)}"


@tool(description="获取最新考勤记录（最多10条），需要提供JWT token")
async def get_latest_attendance(token: str) -> str:
    """获取最新考勤记录工具"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{DJANGO_API_BASE_URL}/home/latest/attendance/",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            data = response.json()
            
            # 验证数据格式
            if not isinstance(data, list):
                return f"获取最新考勤记录失败: 返回数据格式错误，期望列表但得到 {type(data).__name__}"
            
            if not data:
                return "暂无最新考勤记录"
                
            result = "最新考勤记录：\n"
            for record in data:
                # 验证每条记录的格式
                if not isinstance(record, dict):
                    continue
                if 'id' not in record or 'type' not in record or 'status' not in record:
                    continue
                result += f"- ID: {record['id']}, 类型: {record['type']}, 状态: {record['status']}\n"
                if 'start_time' in record and 'end_time' in record:
                    result += f"  时间: {record['start_time']} 至 {record['end_time']}\n"
            return result
    except Exception as e:
        logger.error(f"获取最新考勤记录失败: {str(e)}")
        return f"获取最新考勤记录失败: {str(e)}"


@tool(description="获取部门员工数量统计，需要提供JWT token")
async def get_department_staff_count(token: str) -> str:
    """获取部门员工数量统计工具"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{DJANGO_API_BASE_URL}/home/department/staff/count/",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            data = response.json()
            
            # 验证数据格式
            if not isinstance(data, list):
                return f"获取部门员工数量失败: 返回数据格式错误，期望列表但得到 {type(data).__name__}"
            
            if not data:
                return "暂无部门员工数量统计"
                
            result = "部门员工数量统计：\n"
            for dept in data:
                if not isinstance(dept, dict):
                    continue
                if 'name' not in dept or 'staff_count' not in dept:
                    continue
                result += f"- {dept['name']}: {dept['staff_count']} 人\n"
            return result
    except Exception as e:
        logger.error(f"获取部门员工数量失败: {str(e)}")
        return f"获取部门员工数量失败: {str(e)}"