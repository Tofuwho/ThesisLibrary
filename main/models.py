from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django import forms


class Category(models.Model):
    """Top-level grouping: Undergraduate or Graduate."""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Department(models.Model):
    """Departments under each category (e.g., CICT, CAS)."""
    name = models.CharField(max_length=150)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="departments")

    class Meta:
        unique_together = ("name", "category")

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class Course(models.Model):
    """Courses under each department."""
    name = models.CharField(max_length=150)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="courses")

    class Meta:
        unique_together = ("name", "department")

    def __str__(self):
        return f"{self.name} - {self.department.name}"


class Thesis(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    co_author = models.CharField(max_length=255, blank=True, null=True)
    year = models.IntegerField()
    abstract = models.TextField()
    thesis_type = models.CharField(max_length=100, blank=True)
    specialization = models.CharField(max_length=100, blank=True)

    # Extended metadata
    keywords = models.CharField(max_length=255, blank=True)
    research_category = models.CharField(max_length=50, blank=True)
    expected_completion = models.DateField(null=True, blank=True)

    # Supervisor info
    supervisor_name = models.CharField(max_length=150, blank=True)
    supervisor_email = models.EmailField(blank=True)
    supervisor_department = models.CharField(max_length=150, blank=True)
    supervisor_title = models.CharField(max_length=100, blank=True)
    co_supervisor_name = models.CharField(max_length=150, blank=True)
    co_supervisor_email = models.EmailField(blank=True)

    # Structured co-authors (optional detailed list)
    co_authors = models.JSONField(default=list, blank=True)

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)

    file = models.FileField(upload_to="thesis_files/", blank=True, null=True)  # optional download

    def __str__(self):
        return f"{self.title} ({self.year})"


class RejectedThesis(models.Model):
    """Archive table for rejected thesis submissions."""
    # Original submission data
    original_submission_id = models.PositiveIntegerField(null=True, blank=True, help_text="ID of original submission")
    
    # Thesis information
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    abstract = models.TextField(blank=True)
    thesis_type = models.CharField(max_length=100, blank=True)
    specialization = models.CharField(max_length=120, blank=True)
    
    # Academic classification
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Files
    file = models.FileField(upload_to="thesis_files/rejected/", blank=True, null=True)
    approval_sheet = models.FileField(
        upload_to="thesis_files/rejected_approval_sheets/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "jpg", "jpeg", "png"])],
    )
    
    # Rejection details
    rejection_reason = models.TextField(blank=True, help_text="Reason for rejection")
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rejected_theses",
        help_text="Admin who rejected this submission"
    )
    rejected_at = models.DateTimeField(auto_now_add=True)
    
    # Original submitter info
    original_submitter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rejected_submissions",
        help_text="Original submitter of this thesis"
    )
    
    class Meta:
        ordering = ["-rejected_at"]
        verbose_name = "Rejected Thesis"
        verbose_name_plural = "Rejected Theses"
    
    def __str__(self):
        return f"Rejected: {self.title} ({self.year})"


class Submission(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending Review"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    REVIEW_PENDING = "pending"
    REVIEW_READY = "ready_for_approval"
    REVIEW_RECOMMEND_REJECT = "recommend_reject"

    REVIEW_STATE_CHOICES = [
        (REVIEW_PENDING, "Pending"),
        (REVIEW_READY, "Ready to be approved"),
        (REVIEW_RECOMMEND_REJECT, "Recommend reject"),
    ]

    submitter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="thesis_submissions",
    )

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    abstract = models.TextField(blank=True)
    thesis_type = models.CharField(max_length=100, blank=True)
    specialization = models.CharField(max_length=120, blank=True)

    # Extended metadata from student dashboard
    keywords = models.CharField(max_length=255, blank=True)
    research_category = models.CharField(max_length=50, blank=True)
    expected_completion = models.DateField(null=True, blank=True)

    # Supervisor info
    supervisor_name = models.CharField(max_length=150, blank=True)
    supervisor_email = models.EmailField(blank=True)
    supervisor_department = models.CharField(max_length=150, blank=True)
    supervisor_title = models.CharField(max_length=100, blank=True)
    co_supervisor_name = models.CharField(max_length=150, blank=True)
    co_supervisor_email = models.EmailField(blank=True)

    # Structured co-authors list
    co_authors = models.JSONField(default=list, blank=True)

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)

    file = models.FileField(upload_to="thesis_files/submissions/", blank=True, null=True)

    #  Approval sheet: allows PDF + images (jpg, jpeg, png)
    approval_sheet = models.FileField(
        upload_to="thesis_files/approval_sheets/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "jpg", "jpeg", "png"])],
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    decision_note = models.TextField(blank=True)
    review_state = models.CharField(max_length=30, choices=REVIEW_STATE_CHOICES, default=REVIEW_PENDING)

    class Meta:
        ordering = ["-created_at"]
        db_table = "main_pending_submission"
        verbose_name = "Pending Submission"
        verbose_name_plural = "Pending Submissions"

    def approve(self, approved_by=None):
        """Approve submission: move data to Thesis table and delete from pending submissions."""
        if self.status != self.STATUS_PENDING:
            raise ValueError("Only pending submissions can be approved")
        
        # Create Thesis record
        thesis = Thesis.objects.create(
            title=self.title,
            author=self.author or self.submitter.get_full_name() or self.submitter.get_username(),
            year=self.year or timezone.now().year,
            abstract=self.abstract,
            thesis_type=self.thesis_type,
            specialization=self.specialization,
            keywords=self.keywords,
            research_category=self.research_category,
            expected_completion=self.expected_completion,
            supervisor_name=self.supervisor_name,
            supervisor_email=self.supervisor_email,
            supervisor_department=self.supervisor_department,
            supervisor_title=self.supervisor_title,
            co_supervisor_name=self.co_supervisor_name,
            co_supervisor_email=self.co_supervisor_email,
            co_authors=self.co_authors,
            category=self.category,
            department=self.department,
            course=self.course,
            file=self.file,
        )
        
        # Delete the submission from pending (it's now in Thesis table)
        self.delete()
        return thesis

    def reject(self, rejection_reason: str = "", rejected_by=None):
        """Reject submission: move data to RejectedThesis table and delete from pending submissions."""
        if self.status != self.STATUS_PENDING:
            raise ValueError("Only pending submissions can be rejected")
        
        # Create RejectedThesis record
        rejected_thesis = RejectedThesis.objects.create(
            original_submission_id=self.id,
            title=self.title,
            author=self.author or self.submitter.get_full_name() or self.submitter.get_username(),
            year=self.year or timezone.now().year,
            abstract=self.abstract,
            thesis_type=self.thesis_type,
            specialization=self.specialization,
            category=self.category,
            department=self.department,
            course=self.course,
            file=self.file,
            approval_sheet=self.approval_sheet,
            rejection_reason=rejection_reason,
            rejected_by=rejected_by,
            original_submitter=self.submitter,
        )
        
        # Delete the submission from pending (it's now in RejectedThesis table)
        self.delete()
        return rejected_thesis

    def __str__(self):
        return f"Submission: {self.title} by {self.submitter} [{self.status}]"
