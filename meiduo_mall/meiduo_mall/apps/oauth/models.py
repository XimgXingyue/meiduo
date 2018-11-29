from django.db import models

# Create your models here.
from django.db import models
from meiduo_mall.utils.models import BaseModel


class OAuthQQUser(BaseModel):
    """
    QQ登录用户数据
    """
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='user')
    openid = models.CharField(max_length=64, verbose_name='openid', db_index=True)

    class Meta:
        db_table = 'tb_oauth_qq'
        verbose_name = 'QQ_user login data'
        verbose_name_plural = verbose_name
