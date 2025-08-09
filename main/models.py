from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Thesis(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    year = models.IntegerField()
    abstract = models.TextField()
    thesis_type = models.CharField(max_length=100, blank=True)
    specialization = models.CharField(max_length=100, blank=True)

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)

    file = models.FileField(upload_to='thesis_files/', blank=True, null=True)  # optional download

    def __str__(self):
        return f"{self.title} ({self.year})"
