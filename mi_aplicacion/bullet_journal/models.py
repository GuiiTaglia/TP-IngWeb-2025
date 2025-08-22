from django.db import models
from django.contrib.auth.models import User

class Journal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    title = models.CharField(max_length=200)
    content = models.TextField()
    mood = models.CharField(max_length=50, blank=True)
    sleep_hours = models.FloatField(null=True, blank=True)
    water_glasses = models.IntegerField(null=True, blank=True)
    exercise = models.BooleanField(default=False)
    image = models.ImageField(upload_to='journal_images/', null=True, blank=True)

    def _str_(self):
        return f"{self.title} - {self.user.username}"