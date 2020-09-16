from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

from babies.models import Baby

class User(AbstractUser):
    profile_image = models.CharField(max_length=200) 
    visited_babies = models.ManyToManyField(Baby, through='BabyAccess', related_name='visited_users')


class BabyAccess(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    baby = models.ForeignKey(Baby, on_delete=models.CASCADE)
    last_access_date = models.DateField(auto_now=True)


class Rank(models.Model):
    rank_name = models.CharField(max_length=50)


class Group(models.Model):
    baby = models.ForeignKey(Baby, on_delete=models.CASCADE)
    group_name = models.CharField(max_length=50)
    

class UserBabyRelationship(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    baby = models.ForeignKey(Baby, on_delete=models.CASCADE)
    # 클래스가 지워진다면?
    rank = models.ForeignKey(Rank, on_delete=models.CASCADE)
    # default값은 무소속?
    group = models.ForeignKey(Group, on_delete=models.SET_DEFAULT, default=1)
    relationship_name = models.CharField(max_length=50)