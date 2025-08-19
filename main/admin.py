from django.contrib import admin
from .models import Thesis

@admin.register(Thesis)
class ThesisAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'year', 'thesis_type', 'specialization')
    # Add 'file' to fields if you use fieldsets or fields