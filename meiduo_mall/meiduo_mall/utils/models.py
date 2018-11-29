from django.db import models


class BaseModel(models.Model):

    """为模型类补充字段"""
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="create time")
    update_time = models.DateTimeField(auto_now=True, verbose_name="update time")

    class Meta:
        abstract = True  # 说明是抽象模型类, 用于继承使用，数据库迁移时不会创建BaseModel的表
