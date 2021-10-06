from django.db import models

from nabcommon import singleton_model

# ici on defini le modele de donnes pour la config


class Config(singleton_model.SingletonModel):

    localisation = models.TextField(null=True)
    index_posologie = models.TextField(default="aqi", null=True)
    visual_posologie = models.TextField(default="always", null=True)

    # necessaire pour declencher via le site web
    next_performance_date = models.DateTimeField(null=True)
    next_performance_type = models.TextField(null=True)

    class Meta:
        app_label = "nabposologie"
