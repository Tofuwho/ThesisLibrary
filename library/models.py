from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Thesis(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    year = models.PositiveIntegerField()
    thesis_type = models.CharField(max_length=100)
    specialization = models.CharField(max_length=120, blank=True)
    abstract = models.TextField(blank=True)
    categories = models.ManyToManyField(Category, related_name="theses", blank=True)
    file_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.year})"
