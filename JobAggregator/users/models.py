from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    photo_profile = models.ImageField(upload_to='image_for_users/', default=None, blank=True, null=True)

    def __str__(self):
        return f"{self.username}"

