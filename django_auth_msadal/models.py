from django.db import models


class AuthToken(models.Model):
    username = models.CharField('User', max_length=250, primary_key=True)
    token = models.CharField('Token', max_length=250)
