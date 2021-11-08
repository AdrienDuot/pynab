from django.db import models

from nabcommon import singleton_model

class alarm(models.Model):
    title = models.CharField(max_length=50)
    date = models.DateField()

class Config(singleton_model.SingletonModel):
    enabled = models.BooleanField(default=True)
    enabled = models.models.CharField(max_length=30)
    

    class Meta:
        app_label = "nab8balld"
