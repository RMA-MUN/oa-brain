"""
officeAuth 模型类：
    - 这里主要是对django自带的User模型进行了修改。
    - 移除了不常用的字段，添加了用户状态码来判断用户状态。

不同模型的功能：
    - OfficeUserManager， 用于创建和管理OfficeUser用户，包括了同步和异步创建用户的方法。
    - OfficeUser， 抽象类，定义了OfficeUser用户的基本字段和方法。
    - UserStatusChoice， 枚举类，定义了用户的三种不同状态。
    - OfficeDepartment， 部门模型类，定义了企业内各个部门的基本字段和方法。

"""

from django.contrib import auth
from django.contrib.auth import get_backends
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager
)
from django.db import models
import shortuuid

class UserStatusChoice(models.IntegerChoices):
    """
    用户状态选择
    """
    LOCKED = 2, "已锁定"
    ACTIVE = 1, "已激活"
    DISABLED = 0, "未激活"

class OfficeUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user_object(self, username, email, password, **extra_fields):
        """
        创建并返回一个新的用户对象，而不保存到数据库中。
        """
        if not username:
            raise ValueError("用户名不能为空")

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.password = make_password(password)
        return user

    def _create_user(self, username, email, password, **extra_fields):
        """
        创建并保存一个普通用户，使用提供的用户名、电子邮件和密码。
        """
        user = self._create_user_object(username, email, password, **extra_fields)
        user.save(using=self._db)
        return user

    async def _acreate_user(self, username, email, password, **extra_fields):
        """
        异步创建并保存一个普通用户，使用提供的用户名、电子邮件和密码。
        """
        user = self._create_user_object(username, email, password, **extra_fields)
        await user.asave(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", False)

        # 如果用户的部门是董事会，则调用创建超级用户的方法
        if extra_fields.get('department') == '董事会':
            return self.create_superuser(username, email, password, **extra_fields)

        return self._create_user(username, email, password, **extra_fields)

    create_user.alters_data = True

    async def acreate_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", False)
        return await self._acreate_user(username, email, password, **extra_fields)

    acreate_user.alters_data = True

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """
        创建并保存一个新的超级用户
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("status", UserStatusChoice.ACTIVE)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("超级用户必须设置为is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("超级用户必须设置为is_superuser=True")

        return self._create_user(username, email, password, **extra_fields)

    create_superuser.alters_data = True

    async def acreate_superuser(
            self, username, email=None, password=None, **extra_fields
    ):
        """
        异步创建并保存一个新的超级用户
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("超级用户必须设置为is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("超级用户必须设置为is_superuser=True.")

        return await self._acreate_user(username, email, password, **extra_fields)

    acreate_superuser.alters_data = True

    def with_perm(
            self, perm, is_active=True, include_superusers=True, backend=None, obj=None
    ):
        if backend is None:
            backends = get_backends()
            if len(backends) == 1:
                backend = backends[0]
            else:
                raise ValueError(
                    "您必须提供一个后端，因为有多个后端配置。"
                )
        elif not isinstance(backend, str):
            raise TypeError(
                "后端必须是一个点分导入路径字符串（got %r）" % backend
            )
        else:
            backend = auth.load_backend(backend)
        if hasattr(backend, "with_perm"):
            return backend.with_perm(
                perm,
                is_active=is_active,
                include_superusers=include_superusers,
                obj=obj,
            )
        return self.none()

class OfficeUser(AbstractBaseUser, PermissionsMixin):
    """
    自定义用户模型，继承自AbstractBaseUser和PermissionsMixin
    """
    uuid = models.CharField(
        primary_key=True, 
        unique=True, 
        editable=False, 
        max_length=22,  # shortuuid生成的字符串长度为22
        default=shortuuid.uuid
    )
    username = models.CharField(
        max_length=150,
        unique=False,
    )
    email = models.EmailField(unique=True, blank=False)
    telephone = models.CharField(max_length=11, unique=True,null=True, blank=False)
    is_staff = models.BooleanField(default=True)
    is_active = models.BooleanField(default=False)
    # 用户状态， 只需要关注status字段
    status = models.IntegerField(
        choices=UserStatusChoice,
        default=UserStatusChoice.DISABLED
    )
    date_joined = models.DateTimeField(auto_now_add=True)
    # 部门
    department = models.ForeignKey(
        'OfficeDepartment', on_delete=models.SET_NULL, null=True,
        related_name="users_department", related_query_name="users_department")


    # 确保管理器引用正确
    objects = OfficeUserManager()

    EMAIL_FIELD = "email"
    # 这里的USERNAME_FIELD是用来鉴权的，在authenticate方法中会使用到
    USERNAME_FIELD = "email"
    # 这里的REQUIRED_FIELDS是用来创建用户时必填的字段，在create_user方法中会使用到
    REQUIRED_FIELDS = ["username", "password"]

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username

    class Meta:
        db_table = 'officeAuth_officeuser'


class OfficeDepartment(models.Model):
    """
    部门模型，
    包含部门的基本信息，
    如部门名称、部门描述、部门负责人等。
    """
    name = models.CharField(max_length=100)
    introduction = models.TextField(max_length=500)
    # 部门负责人
    leader = models.OneToOneField(
        OfficeUser, null=True, on_delete=models.SET_NULL,
        related_name="leader_department", related_query_name="leader_department")

    # manager，高级管理层
    manager = models.ForeignKey(
        OfficeUser, null=True, on_delete=models.SET_NULL,
        related_name="manager_department", related_query_name="manager_department")
    
    # 在数据库中存储leader和manager的名字
    leader_name = models.CharField(max_length=100, blank=True, null=True)
    manager_name = models.CharField(max_length=100, blank=True, null=True)
    
    # 根据leader_id和manager_id查询到用户的username
    def get_name_by_id(self, user_id):
        try:
            user = OfficeUser.objects.get(uuid=user_id)
            return user.username
        except OfficeUser.DoesNotExist:
            return None
    
    # 重写save方法以确保数据一致性
    def save(self, *args, **kwargs):
        # 更新leader和manager的名字
        if self.leader:
            self.leader_name = self.leader.username
        else:
            self.leader_name = None
        
        if self.manager:
            self.manager_name = self.manager.username
        else:
            self.manager_name = None
            
        super().save(*args, **kwargs)
        
    class Meta:
        # 添加排序规则，按照id升序排列，确保分页结果一致
        ordering = ['id']