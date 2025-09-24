from django.db import models
from django.contrib.auth.models import User
#from cloudinary_storage.storage import RawMediaCloudinaryStorage  deje esto aca por si usamos pdf en algun momento

class Journal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    mood = models.CharField(max_length=50)
    sleep_hours = models.FloatField(null=True)
    water_glasses = models.IntegerField(null=True)
    exercise = models.BooleanField(default=False)
    image = models.ImageField(upload_to='journal_images/', null=True, blank=True)
    #esto solo si queremos pdf --> pruebas_en_pdf = models.FileField(upload_to='raw/', blank=True) Adicionalmente, si necesitamos manejar archivos PDF o ZIP debemos habilitar la opción de CLoudinary que permite esto en la pestaña Seguiridad
    # y esto por si queremos video: video = models.FileField(upload_to='videos/noticias',blank=True)

    def __str__(self):
        return f"{self.date} - {self.user.username}"
    
