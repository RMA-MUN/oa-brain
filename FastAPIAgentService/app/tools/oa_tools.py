"""
智能体可以调用的工具，负责处理OA相关的任务
"""
import os

import httpx
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

load_dotenv()

# Django API基础URL
DJANGO_API_BASE_URL = os.getenv("DJANGO_API_BASE_URL")


# 考勤相关工具
@tool(description="获取考勤类型列表，不需要参数")
async def get_attendance_types() -> str:
    """获取考勤类型列表工具"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{DJANGO_API_BASE_URL}/Attendance/attendance-type/")
            response.raise_for_status()
            data = response.json()
            return f"考勤类型列表：\n" + "\n".join([f"- {item['name']} (ID: {item['id']})" for item in data])
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
            
            result = "考勤记录列表：\n"
            for record in data:
                result += f"- ID: {record['id']}, 类型: {record['type']}, 状态: {record['status']}\n"
                result += f"  时间: {record['start_time']} 至 {record['end_time']}\n"
                if record.get('reason'):
                    result += f"  原因: {record['reason']}\n"
            return result
    except Exception as e:
        logger.error(f"获取考勤记录失败: {str(e)}")
        return f"获取考勤记录失败: {str(e)}"


@tool(description="创建考勤记录，需要提供JWT token和考勤信息（type, start_time, end_time, reason, responser）")
async def create_attendance_record(
    token: str,
    attendance_data: AttendanceCreateRequest
) -> str:
    """创建考勤记录工具"""
    try:
        request_data = attendance_data.model_dump()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DJANGO_API_BASE_URL}/Attendance/attendance/",
                headers={"Authorization": f"Bearer {token}"},
                json=request_data
            )
            response.raise_for_status()
            data = response.json()
            return f"考勤记录创建成功！\nID: {data['id']}\n类型: {data['type']}\n状态: {data['status']}"
    except Exception as e:
        logger.error(f"创建考勤记录失败: {str(e)}")
        return f"创建考勤记录失败: {str(e)}"


@tool(description="更新考勤记录状态，需要提供JWT token、记录ID和更新信息（status, comment）")
async def update_attendance_record(
    token: str,
    record_id: int,
    update_data: AttendanceUpdateRequest
) -> str:
    """更新考勤记录状态工具"""
    try:
        request_data = update_data.model_dump(exclude_unset=True)
        
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
            
            result = "部门列表：\n"
            for dept in data:
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
            
            result = "用户列表（按部门分组）：\n"
            for dept_name, dept_data in data.items():
                result += f"\n【{dept_name}】\n"
                if dept_data.get("leader"):
                    result += "负责人：\n"
                    for leader in dept_data["leader"]:
                        result += f"- {leader['username']} ({leader['email']})\n"
                if dept_data.get("members"):
                    result += "成员：\n"
                    for member in dept_data["members"]:
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
            
            result = f"通知列表（第{page}页，共{data.get('count', 0)}条）：\n"
            for inform in data.get("results", []):
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
    inform_data: InformCreateRequest
) -> str:
    """创建通知工具"""
    try:
        request_data = inform_data.model_dump(exclude_unset=True)
        
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
    update_data: InformUpdateRequest
) -> str:
    """更新通知工具"""
    try:
        request_data = update_data.model_dump(exclude_unset=True)
        
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
            
            result = "最新通知：\n"
            for inform in data:
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
            
            result = "最新考勤记录：\n"
            for record in data:
                result += f"- ID: {record['id']}, 类型: {record['type']}, 状态: {record['status']}\n"
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
            
            result = "部门员工数量统计：\n"
            for dept in data:
                result += f"- {dept['name']}: {dept['staff_count']} 人\n"
            return result
    except Exception as e:
        logger.error(f"获取部门员工数量失败: {str(e)}")
        return f"获取部门员工数量失败: {str(e)}"
