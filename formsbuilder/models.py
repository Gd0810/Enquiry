from django.db import models
import uuid
from django.core.exceptions import ValidationError

# Assuming STATUS_CHOICES and FIELD_TYPES are defined
STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('in_progress', 'In Progress'),
    ('on_hold', 'On Hold'),
    ('resolved', 'Resolved'),
    ('rejected', 'Rejected'),
]

FIELD_TYPES = [
    ('text', 'Text'),
    ('email', 'Email'),
    ('number', 'Number'),
    ('date', 'Date'),
    ('time', 'Time'),
    ('textarea', 'Textarea'),
    ('select', 'Select'),
    ('password', 'Password'),
    ('checkbox', 'Checkbox'),
    ('radio', 'Radio'),
    ('file', 'File'),
    ('range', 'Range'),
    ('tel', 'Telephone'),
    ('url', 'URL'),
    ('hidden', 'Hidden'),
    ('color', 'Color'),
    ('submit', 'Submit'),
    ('reset', 'Reset'),
    ('button', 'Button'),
]

class Department(models.Model):
    name = models.CharField(max_length=255)
    dep_email = models.EmailField()
    dep_phone = models.CharField(max_length=20, blank=True, null=True)
    dep_img = models.ImageField(upload_to='department_images/', blank=True, null=True)

    def __str__(self):
        return self.name

class DynamicForm(models.Model):
    name = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

class FormField(models.Model):
    form = models.ForeignKey(DynamicForm, related_name="fields", on_delete=models.CASCADE)
    label = models.CharField(max_length=255)
    field_type = models.CharField(max_length=50, choices=FIELD_TYPES)
    options = models.TextField(blank=True, null=True, help_text="Comma-separated options for select, checkbox, or radio fields")
    required = models.BooleanField(default=False)
    max_file_size_mb = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Maximum file size in megabytes (for file fields only).",
        verbose_name="Max File Size (MB)"
    )

    def clean(self):
        # Validate max_file_size_mb for file fields
        if self.field_type == 'file' and self.required and not self.max_file_size_mb:
            raise ValidationError({'max_file_size_mb': 'Maximum file size is required for required file fields.'})
        if self.field_type != 'file' and self.max_file_size_mb:
            raise ValidationError({'max_file_size_mb': 'Maximum file size should only be set for file fields.'})
        if self.max_file_size_mb and self.max_file_size_mb <= 0:
            raise ValidationError({'max_file_size_mb': 'Maximum file size must be a positive integer.'})

    @property
    def option_list(self):
        if self.options:
            return [opt.strip() for opt in self.options.split(",")]
        return []

    def __str__(self):
        return f"{self.label} ({self.field_type})"

class Enquiry(models.Model):
    form = models.ForeignKey(DynamicForm, on_delete=models.CASCADE)
    data = models.JSONField()
    register_number = models.SlugField(unique=True, default=uuid.uuid4)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reply = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.register_number

class DepartmentAdminAssignment(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.department.name if self.department else 'No Department'}"
    

class ChatbotQA(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    question = models.CharField(max_length=255)
    answer = models.TextField()

    def __str__(self):
        return self.question

class ChatbotSettings(models.Model):
    is_enabled = models.BooleanField(default=True, verbose_name="Chatbot status")

    class Meta:
        verbose_name = "Chatbot Settings"
        verbose_name_plural = "Chatbot Settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj    