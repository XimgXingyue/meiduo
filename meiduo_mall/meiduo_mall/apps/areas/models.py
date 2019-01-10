from django.db import models

# Create your models here.
class Area(models.Model):
    '''
    行政区划
    '''
    name = models.CharField(max_length=20, verbose_name='name')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='subs', null=True, verbose_name='parent_area')

    class Meta:
        db_table = 'tb_areas'
        verbose_name = 'Administrative division'
        verbose_name_plural = 'Administrative division'

    def __str__(self):
        return self.name

