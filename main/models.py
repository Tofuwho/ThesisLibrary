from django.db import models
from django.conf import settings
from django.utils import timezone


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


class Submission(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_SUBMITTED = 'submitted'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    submitter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='thesis_submissions'
    )

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    abstract = models.TextField(blank=True)
    thesis_type = models.CharField(max_length=100, blank=True)
    specialization = models.CharField(max_length=120, blank=True)

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)

    file = models.FileField(upload_to='thesis_files/submissions/', blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUBMITTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    decision_note = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def approve(self):
        """Mark this submission as approved and return the created Thesis instance."""
        thesis = Thesis.objects.create(
            title=self.title,
            author=self.author or self.submitter.get_full_name() or self.submitter.get_username(),
            year=self.year or timezone.now().year,
            abstract=self.abstract,
            thesis_type=self.thesis_type,
            specialization=self.specialization,
            category=self.category,
            file=self.file,
        )
        self.status = self.STATUS_APPROVED
        self.approved_at = timezone.now()
        self.save(update_fields=['status', 'approved_at', 'updated_at'])
        return thesis

    def reject(self, note: str = ""):
        self.status = self.STATUS_REJECTED
        self.decision_note = note
        self.save(update_fields=['status', 'decision_note', 'updated_at'])

    def __str__(self):
        return f"Submission: {self.title} by {self.submitter} [{self.status}]"
