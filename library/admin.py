from django.contrib import admin
from .models import Thesis, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Thesis)
class ThesisAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "year", "thesis_type", "specialization")
    list_filter = ("year", "thesis_type", "specialization", "categories")
    search_fields = ("title", "author", "abstract")
    filter_horizontal = ("categories",)
