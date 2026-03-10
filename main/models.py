from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django import forms
from django.contrib.auth.models import User

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

    # Foreign keys
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)

    lc_classification = models.CharField(max_length=100, blank=True, null=True, help_text="Library of Congress Classification")

    # File upload
    file = models.FileField(upload_to="thesis_files/", blank=True, null=True)

    def __str__(self):
        return f"{self.title} ({self.year})"
    
    def get_coauthor_names(self):
        """Return a list of formatted co-author names for display."""
        coauthors = []
        for coauthor in self.co_authors.all():
            name_parts = []
            if coauthor.first_name:
                name_parts.append(coauthor.first_name)
            if coauthor.last_name:
                name_parts.append(coauthor.last_name)
            
            if name_parts:
                coauthors.append(' '.join(name_parts))
            elif coauthor.student_id:
                coauthors.append(f"Student ID: {coauthor.student_id}")
            else:
                coauthors.append("Unnamed Co-Author")
        return coauthors
    
    def get_coauthor_details(self):
        """Return detailed co-author information for admin display."""
        coauthors = []
        for coauthor in self.co_authors.all():
            details = {
                'id': coauthor.id,
                'first_name': coauthor.first_name,
                'last_name': coauthor.last_name,
                'student_id': coauthor.student_id,
                'email': coauthor.email,
                'full_name': f"{coauthor.first_name} {coauthor.last_name}".strip() or "Unnamed Co-Author"
            }
            coauthors.append(details)
        return coauthors

class CoAuthor(models.Model):
    """Relational co-authors linked to an approved Thesis."""
    thesis = models.ForeignKey(Thesis, related_name="co_authors", on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    student_id = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or "Unnamed Co-Author"
        
class SubmissionCoAuthor(models.Model):
    """Relational co-authors linked to a Submission (before approval)."""
    submission = models.ForeignKey("Submission", related_name="co_authors", on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    student_id = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or "Unnamed Submission Co-Author"

class DownloadLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    thesis = models.ForeignKey(Thesis, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} downloaded {self.thesis.title} at {self.timestamp}"


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

    # Extended metadata from submission portal
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
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    lc_classification = models.CharField(max_length=100, blank=True, null=True, help_text="Library of Congress Classification")

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

    def approve(self, approved_by=None, lc_classification=None):
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
            category=self.category,
            department=self.department,
            course=self.course,
            lc_classification=lc_classification or self.lc_classification,
            file=self.file,
        )

        # Copy relational co-authors into Thesis
        for ca in self.co_authors.all():
            CoAuthor.objects.create(
                thesis=thesis,
                first_name=ca.first_name,
                last_name=ca.last_name,
                student_id=ca.student_id,
                email=ca.email,
            )

        # Keep submission record for student history
        self.status = self.STATUS_APPROVED
        self.approved_at = timezone.now()
        self.save(update_fields=["status", "approved_at"])
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
        
        # Keep submission record and mark as rejected
        self.status = self.STATUS_REJECTED
        self.decision_note = rejection_reason or self.decision_note
        self.save(update_fields=["status", "decision_note"])
        return rejected_thesis

    def get_coauthor_names(self):
        """Return a list of formatted co-author names for display."""
        coauthors = []
        for coauthor in self.co_authors.all():
            name_parts = []
            if coauthor.first_name:
                name_parts.append(coauthor.first_name)
            if coauthor.last_name:
                name_parts.append(coauthor.last_name)
            
            if name_parts:
                coauthors.append(' '.join(name_parts))
            elif coauthor.student_id:
                coauthors.append(f"Student ID: {coauthor.student_id}")
            else:
                coauthors.append("Unnamed Co-Author")
        return coauthors
    
    def get_coauthor_details(self):
        """Return detailed co-author information for admin display."""
        coauthors = []
        for coauthor in self.co_authors.all():
            details = {
                'id': coauthor.id,
                'first_name': coauthor.first_name,
                'last_name': coauthor.last_name,
                'student_id': coauthor.student_id,
                'email': coauthor.email,
                'full_name': f"{coauthor.first_name} {coauthor.last_name}".strip() or "Unnamed Co-Author"
            }
            coauthors.append(details)
        return coauthors

    def __str__(self):
        return f"Submission: {self.title} by {self.submitter} [{self.status}]"


class Student(models.Model):
    """Student database - stores student IDs for verification"""
    student_id = models.CharField(max_length=50, unique=True, primary_key=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"
    
    def __str__(self):
        return f"{self.student_id} - {self.first_name} {self.last_name}".strip() or self.student_id


class Professor(models.Model):
    """Professor database - stores professor IDs for verification"""
    professor_id = models.CharField(max_length=50, unique=True, primary_key=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Professor"
        verbose_name_plural = "Professors"
    
    def __str__(self):
        return f"{self.professor_id} - {self.first_name} {self.last_name}".strip() or self.professor_id


class Librarian(models.Model):
    """Librarian database - stores librarian IDs for verification"""
    librarian_id = models.CharField(max_length=50, unique=True, primary_key=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Librarian"
        verbose_name_plural = "Librarians"
    
    def __str__(self):
        return f"{self.librarian_id} - {self.first_name} {self.last_name}".strip() or self.librarian_id


class AdminStaff(models.Model):
    """Admin Staff database - stores admin IDs for verification"""
    admin_id = models.CharField(max_length=50, unique=True, primary_key=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Admin Staff"
        verbose_name_plural = "Admin Staffs"
    
    def __str__(self):
        return f"{self.admin_id} - {self.first_name} {self.last_name}".strip() or self.admin_id


class VerificationCode(models.Model):
    """Stores verification codes for email verification"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification_code')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Verification Code"
        verbose_name_plural = "Verification Codes"
    
    def __str__(self):
        return f"Code for {self.user.username} - {self.code}"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at


class PasswordResetCode(models.Model):
    """Stores password reset codes for password recovery"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_codes')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Password Reset Code"
        verbose_name_plural = "Password Reset Codes"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reset code for {self.user.username} - {self.code}"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at