from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.
class User(AbstractUser):
    '''
    user info
    '''

    mobile = models.CharField(max_length=11, unique=True, verbose_name="Phone Number")

    class Mate:
        db_table = "tb_users"
        verbose_name = "User Info"
        verbose_name_plural = verbose_name
