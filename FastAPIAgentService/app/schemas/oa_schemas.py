from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# 认证相关schemas
class LoginRequest(BaseModel):
    """登录接口请求模型
    API: /officeAuth/login/
    """
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserInfo(BaseModel):
    """用户信息模型
    用于多个接口的用户信息返回
    """
    uuid: str
    username: str
    email: EmailStr
    department: str


class LoginResponse(BaseModel):
    """登录接口响应模型
    API: /officeAuth/login/
    """
    message: str
    user: UserInfo
    token: str


class ResetPasswordRequest(BaseModel):
    """重置密码接口请求模型
    API: /officeAuth/reset-password/
    """
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., description="新密码")
    confirm_password: str = Field(..., description="确认新密码")


class ResetPasswordResponse(BaseModel):
    """重置密码接口响应模型
    API: /officeAuth/reset-password/
    """
    message: str


class RefreshTokenRequest(BaseModel):
    """刷新Token接口请求模型
    API: /officeAuth/refresh-token/
    """
    token: str = Field(..., description="旧Token")


class RefreshTokenResponse(BaseModel):
    """刷新Token接口响应模型
    API: /officeAuth/refresh-token/
    """
    message: str
    token: str
    expire_time: int


class UserDetailResponse(BaseModel):
    """获取用户详情接口响应模型
    API: /officeAuth/user/detail/
    """
    message: str
    user: UserInfo


class UpdateDepartmentLeaderRequest(BaseModel):
    """更新部门领导接口请求模型
    API: /officeAuth/department/update-leader/
    """
    department_id: int = Field(..., description="部门ID")
    new_leader_id: str = Field(..., description="新领导ID")


class UpdateDepartmentLeaderResponse(BaseModel):
    """更新部门领导接口响应模型
    API: /officeAuth/department/update-leader/
    """
    message: str
    department: str
    old_leader: str
    new_leader: str


# 考勤相关schemas
class AttendanceType(BaseModel):
    """考勤类型模型
    API: /Attendance/attendance-type/
    """
    id: int
    name: str


class AttendanceTypeListResponse(List[AttendanceType]):
    """考勤类型列表响应模型
    API: /Attendance/attendance-type/
    """
    pass


class AttendanceResponserResponse(BaseModel):
    """考勤审批人接口响应模型
    API: /Attendance/attendance-responser/
    """
    uuid: str
    username: str
    email: EmailStr


class AttendanceCreateRequest(BaseModel):
    """考勤记录创建请求模型
    API: /Attendance/attendance/ (POST)
    """
    type: int = Field(..., description="考勤类型ID")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    reason: str = Field(..., description="请假原因")
    responser: str = Field(..., description="审批人ID")


class AttendanceUpdateRequest(BaseModel):
    """考勤记录更新请求模型
    API: /Attendance/attendance/ (PUT)
    """
    status: str = Field(..., description="审批状态", pattern="^(approved|rejected)$")
    comment: Optional[str] = Field(None, description="审批意见")


class AttendanceRecord(BaseModel):
    """考勤记录模型
    API: /Attendance/attendance/
    """
    id: int
    type: str
    start_time: datetime
    end_time: datetime
    reason: str
    status: str
    responser: Optional[str] = None
    comment: Optional[str] = None
    create_time: Optional[datetime] = None


class AttendanceListResponse(List[AttendanceRecord]):
    """考勤记录列表响应模型
    API: /Attendance/attendance/ (GET)
    """
    pass


# 员工管理相关schemas
class DepartmentMember(BaseModel):
    """部门成员模型
    API: /staff/department/
    """
    id: int
    name: str
    leader: str
    members: List[str]


class DepartmentListResponse(List[DepartmentMember]):
    """部门列表响应模型
    API: /staff/department/
    """
    pass


class UserMember(BaseModel):
    """用户成员模型
    用于用户列表接口
    """
    uuid: str
    username: str
    email: EmailStr


class DepartmentUsers(BaseModel):
    """部门用户模型
    API: /staff/user/
    """
    leader: List[UserMember]
    members: List[UserMember]


class UserListResponse(Dict[str, DepartmentUsers]):
    """用户列表响应模型
    API: /staff/user/
    """
    pass


class AddStaffRequest(BaseModel):
    """添加员工接口请求模型
    API: /staff/staff/ (POST)
    """
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    email: EmailStr = Field(..., description="邮箱")


class AddStaffResponse(BaseModel):
    """添加员工接口响应模型
    API: /staff/staff/ (POST)
    """
    message: str


class ActivateEmailRequest(BaseModel):
    """激活邮箱接口请求模型
    API: /staff/staff/activate/ (POST)
    """
    password: str = Field(..., description="密码")


class ActivateEmailResponse(BaseModel):
    """激活邮箱接口响应模型
    API: /staff/staff/activate/ (POST)
    """
    message: str


class EditStaffRequest(BaseModel):
    """编辑员工接口请求模型
    API: /staff/staff/edit/<uuid>/ (PUT)
    """
    username: Optional[str] = Field(None, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    department: Optional[int] = Field(None, description="部门ID")


class EditStaffResponse(BaseModel):
    """编辑员工接口响应模型
    API: /staff/staff/edit/<uuid>/ (PUT)
    """
    message: str
    data: Dict[str, Any]


# 文件上传相关schemas
class FileUploadResponse(BaseModel):
    """文件上传接口响应模型
    API: /file/upload/
    """
    errno: int
    data: Dict[str, str]


# 通知相关schemas
class InformCreateRequest(BaseModel):
    """通知创建请求模型
    API: /inform/inform/ (POST)
    """
    title: str = Field(..., description="标题")
    content: str = Field(..., description="内容")
    public: bool = Field(False, description="是否公开")
    department_ids: Optional[List[int]] = Field(None, description="部门ID列表")


class InformUpdateRequest(BaseModel):
    """通知更新请求模型
    API: /inform/inform/ (PUT)
    """
    title: Optional[str] = Field(None, description="标题")
    content: Optional[str] = Field(None, description="内容")
    public: Optional[bool] = Field(None, description="是否公开")
    department_ids: Optional[List[int]] = Field(None, description="部门ID列表")


class Inform(BaseModel):
    """通知模型
    API: /inform/inform/
    """
    id: int
    title: str
    content: str
    public: bool
    department_ids: Optional[List[int]] = None
    create_time: datetime


class InformListResponse(List[Inform]):
    """通知列表响应模型
    API: /inform/inform/ (GET)
    """
    pass


# 首页相关schemas
class LatestInform(BaseModel):
    """最新通知模型
    API: /home/latest/inform/
    """
    id: int
    title: str
    content: str
    create_time: datetime


class LatestInformResponse(List[LatestInform]):
    """最新通知响应模型
    API: /home/latest/inform/
    """
    pass


class LatestAttendance(BaseModel):
    """最新考勤记录模型
    API: /home/latest/attendance/
    """
    id: int
    type: str
    start_time: datetime
    end_time: datetime
    status: str


class LatestAttendanceResponse(List[LatestAttendance]):
    """最新考勤记录响应模型
    API: /home/latest/attendance/
    """
    pass


class DepartmentStaffCount(BaseModel):
    """部门员工数量模型
    API: /home/department/staff/count/
    """
    name: str
    staff_count: int


class DepartmentStaffCountResponse(List[DepartmentStaffCount]):
    """部门员工数量响应模型
    API: /home/department/staff/count/
    """
    pass