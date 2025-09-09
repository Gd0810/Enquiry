# admin.py (updated)
from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
from django.utils.safestring import mark_safe
from django import forms
from .models import Department, DynamicForm, FormField, DepartmentAdminAssignment, Enquiry, ChatbotQA, ChatbotSettings
from .utils.email import send_async_email
import logging
import json

# Set up logging
logger = logging.getLogger(__name__)

class FormFieldForm(forms.ModelForm):
    class Meta:
        model = FormField
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make max_file_size_mb visible only for file fields
        if self.instance and self.instance.field_type != 'file':
            self.fields['max_file_size_mb'].widget = forms.HiddenInput()

class FormFieldInline(admin.TabularInline):
    model = FormField
    extra = 1
    form = FormFieldForm

# Define approve_admins action
def approve_admins(modeladmin, request, queryset):
    logger.debug("[⚠️] approve_admins called!")
    for assignment in queryset:
        if not assignment.approved and assignment.department:
            assignment.approved = True
            assignment.save()
            logger.debug(f"[📧] Attempting to send email to: {assignment.user.email}")

            subject = "Department Admin Access Approved"

            # Plain text fallback
            text_message = (
                f"Dear {assignment.user.username},\n\n"
                f"Your request for department admin access has been approved for {assignment.department.name}.\n"
                f"Access your dashboard here: {request.build_absolute_uri('/dashboard/')}\n\n"
                "Best regards,\nSystem Administration Team"
            )

            # Professional HTML email template
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Admin Access Approved</title>
            </head>
            <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; line-height: 1.6;">
                <div style="max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden;">
                    
                    <!-- Header Section -->
                    <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 40px 30px; text-align: center; color: white;">
                        <h1 style="margin: 0; font-size: 28px; font-weight: 600; letter-spacing: -0.5px;">Access Approved</h1>
                        <p style="margin: 8px 0 0 0; font-size: 16px; opacity: 0.9;">Your admin privileges have been activated</p>
                    </div>
                    
                    <!-- Content Section -->
                    <div style="padding: 40px 30px;">
                        <div style="margin-bottom: 30px;">
                            <p style="font-size: 16px; color: #374151; margin: 0 0 8px 0;">Dear <strong>{assignment.user.username}</strong>,</p>
                            <p style="font-size: 16px; color: #6b7280; margin: 0; line-height: 1.5;">Congratulations! Your request for department administrator access has been approved. You now have full administrative privileges for your assigned department.</p>
                        </div>
                        
                        <!-- Approval Details -->
                        <div style="background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%); border-left: 4px solid #10b981; padding: 25px; margin: 30px 0; border-radius: 0 8px 8px 0;">
                            <h3 style="margin: 0 0 20px 0; font-size: 18px; color: #065f46; font-weight: 600;">Admin Assignment Details</h3>
                            
                            <div style="display: table; width: 100%; border-collapse: collapse;">
                                <div style="display: table-row;">
                                    <div style="display: table-cell; padding: 8px 0; width: 120px; font-weight: 600; color: #374151; font-size: 14px;">Department:</div>
                                    <div style="display: table-cell; padding: 8px 0; color: #1f2937; font-size: 14px; font-weight: 600;">{assignment.department.name}</div>
                                </div>
                                <div style="display: table-row;">
                                    <div style="display: table-cell; padding: 8px 0; width: 120px; font-weight: 600; color: #374151; font-size: 14px;">Role:</div>
                                    <div style="display: table-cell; padding: 8px 0; color: #1f2937; font-size: 14px;">Department Administrator</div>
                                </div>
                                <div style="display: table-row;">
                                    <div style="display: table-cell; padding: 8px 0; width: 120px; font-weight: 600; color: #374151; font-size: 14px;">Status:</div>
                                    <div style="display: table-cell; padding: 8px 0;">
                                        <span style="background-color: #10b981; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Active</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Access Information -->
                        <div style="background-color: #eff6ff; border: 1px solid #dbeafe; border-radius: 8px; padding: 25px; margin: 30px 0;">
                            <h4 style="margin: 0 0 15px 0; font-size: 16px; color: #1e40af; font-weight: 600;">Your Admin Privileges</h4>
                            <ul style="margin: 0; padding-left: 20px; color: #374151; font-size: 14px; line-height: 1.8;">
                                <li>Manage department enquiries and requests</li>
                                <li>Review and respond to user submissions</li>
                                <li>Access department dashboard and analytics</li>
                                <li>Update department information and settings</li>
                                <li>Monitor department activity and reports</li>
                            </ul>
                        </div>
                        
                        <!-- Call to Action -->
                        <div style="text-align: center; margin: 35px 0;">
                            <a href="{request.build_absolute_uri('/dashboard/')}" 
                               style="display: inline-block; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; letter-spacing: 0.3px; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);">
                                Access Your Dashboard
                            </a>
                        </div>
                        
                        <!-- Next Steps -->
                        <div style="background-color: #fefce8; border: 1px solid #fde047; border-radius: 8px; padding: 20px; margin: 30px 0;">
                            <h4 style="margin: 0 0 12px 0; font-size: 16px; color: #a16207; font-weight: 600;">Getting Started</h4>
                            <p style="margin: 0; font-size: 14px; color: #92400e; line-height: 1.6;">
                                Log in to your dashboard to familiarize yourself with the admin interface. If you need assistance or have questions about your new role, please don't hesitate to contact our support team.
                            </p>
                        </div>
                        
                        <div style="margin-top: 40px; padding-top: 30px; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0 0 8px 0; font-size: 16px; color: #374151;">Best regards,</p>
                            <p style="margin: 0; font-size: 16px; font-weight: 600; color: #111827;">System Administration Team</p>
                            <p style="margin: 5px 0 0 0; font-size: 14px; color: #6b7280;">{request.get_host()}</p>
                        </div>
                    </div>
                    
                    <!-- Footer -->
                    <div style="background-color: #f3f4f6; padding: 25px 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                        <p style="margin: 0; font-size: 12px; color: #6b7280;">
                            This is an automated system notification. Your admin access is now active.<br>
                            For support or questions, please contact the system administrator.
                        </p>
                    </div>
                    
                </div>
            </body>
            </html>
            """

            from_email = settings.EMAIL_HOST_USER
            to_list = [assignment.user.email]

            try:
                # Send email with HTML + fallback text
                send_async_email(subject, text_message, from_email, to_list, html_message)
                logger.debug(f"[✅] Email queued to: {assignment.user.email}")
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
    inlines = [FormFieldInline]

@admin.register(FormField)
class FormFieldAdmin(admin.ModelAdmin):
    list_display = ('label', 'form', 'field_type', 'required', 'max_file_size_mb')
    list_filter = ('field_type', 'required')
    search_fields = ('label', 'form__name')
    form = FormFieldForm

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
    list_display = ('register_number', 'form', 'department', 'status', 'created_at', 'name')
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

@admin.register(ChatbotQA)
class ChatbotQAAdmin(admin.ModelAdmin):
    list_display = ('question', 'department')
    list_filter = ('department',)
    search_fields = ('question', 'answer')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            assignment = DepartmentAdminAssignment.objects.filter(user=request.user, approved=True, department__isnull=False).first()
            if assignment and assignment.department:
                qs = qs.filter(department=assignment.department)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'department' and not request.user.is_superuser:
            assignment = DepartmentAdminAssignment.objects.filter(user=request.user, approved=True, department__isnull=False).first()
            if assignment and assignment.department:
                kwargs['queryset'] = Department.objects.filter(pk=assignment.department.pk)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(ChatbotSettings)
class ChatbotSettingsAdmin(admin.ModelAdmin):
    list_display = ('is_enabled',)
    

    def has_add_permission(self, request):
        return False if self.model.objects.exists() else True

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.none()
        return qs

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser