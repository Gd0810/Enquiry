from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
from .models import Department, DynamicForm, FormField, DepartmentAdminAssignment, Enquiry
from .utils.email import send_async_email
import logging
import json

# Set up logging
logger = logging.getLogger(__name__)

class FormFieldInline(admin.TabularInline):
    model = FormField
    extra = 1

class EnquiryInline(admin.TabularInline):
    model = Enquiry
    extra = 0
    fields = ('register_number', 'status', 'reply')
    readonly_fields = ('register_number',)

# Define approve_admins action
def approve_admins(modeladmin, request, queryset):
    logger.debug("[⚠️] approve_admins called!")
    for assignment in queryset:
        if not assignment.approved and assignment.department:
            assignment.approved = True
            assignment.save()
            logger.debug(f"[📧] Attempting to send email to: {assignment.user.email}")
            subject = "Department Admin Approval"
            message = f"Greeting {assignment.user.username},\nYou are approved as admin for {assignment.department.name}.\nAccess dashboard now at {request.build_absolute_uri('/dashboard/')}."
            from_email = settings.EMAIL_HOST_USER
            to_list = [assignment.user.email]
            try:
                send_async_email(subject, message, from_email, to_list)
                logger.debug(f"[✅] Email sent to: {assignment.user.email}")
            except Exception as e:
                logger.error(f"[❌] Failed to send email to {assignment.user.email}: {str(e)}")
        else:
            logger.warning(f"[⚠️] Skipped approval for {assignment.user.username}: already approved or no department assigned")
    modeladmin.message_user(request, "Selected department admins have been approved and notified.")
approve_admins.short_description = "Approve selected department admins"

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "dep_email", "dep_phone")
    search_fields = ("name", "dep_email")

@admin.register(DynamicForm)
class DynamicFormAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "website")
    list_filter = ("department",)
    search_fields = ("name", "website")
    inlines = [FormFieldInline, EnquiryInline]

@admin.register(DepartmentAdminAssignment)
class DepartmentAdminAssignmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'approved')
    list_filter = ('approved',)
    search_fields = ('user__username', 'department__name')
    actions = [approve_admins]
    fields = ('user', 'department', 'approved')
    readonly_fields = ('user',)

    def get_readonly_fields(self, request, obj=None):
        # Allow department to be set in the form when creating or editing
        if obj:  # Editing an existing object
            return self.readonly_fields
        return ()  # Allow all fields when creating

@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ('register_number', 'form', 'department', 'status', 'created_at', 'name', 'email', 'display_data')
    list_filter = ('status', 'form__department', 'created_at')
    search_fields = ('register_number', 'data__Name', 'data__Email', 'data__What the Enquiry', 'data__courese')
    list_select_related = ('form', 'form__department')
    fields = ('register_number', 'form', 'status', 'reply', 'data', 'created_at')
    readonly_fields = ('register_number', 'data', 'created_at')

    def department(self, obj):
        return obj.form.department
    department.short_description = 'Department'

    def name(self, obj):
        return obj.data.get('Name', 'N/A')
    name.short_description = 'Name'

    def email(self, obj):
        return obj.data.get('Email', 'N/A')
    email.short_description = 'Email'

    def display_data(self, obj):
        # Format JSON data for readability
        try:
            data = obj.data
            formatted_data = []
            for key, value in data.items():
                if isinstance(value, list):
                    value = ', '.join(str(v) for v in value)  # Join lists (e.g., ['python', 'django'] -> 'python, django')
                elif isinstance(value, dict):
                    value = json.dumps(value, indent=2)  # Format nested JSON
                elif value is None:
                    value = 'N/A'
                formatted_data.append(f"{key}: {value}")
            return '\n'.join(formatted_data) or 'No data'
        except Exception as e:
            logger.error(f"Error formatting Enquiry data for {obj.register_number}: {str(e)}")
            return 'Error displaying data'
    display_data.short_description = 'Form Data'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            assignment = DepartmentAdminAssignment.objects.filter(user=request.user, approved=True, department__isnull=False).first()
            if assignment:
                queryset = queryset.filter(form__department=assignment.department)
        return queryset