from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from urllib.parse import urlencode
from django.core.mail import send_mail
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .models import Department, DynamicForm, Enquiry, DepartmentAdminAssignment, STATUS_CHOICES
from .forms import DepartmentAdminRegistrationForm, EnquiryForm
from .utils.email import send_async_email
import json
from django import forms
from django.core.paginator import Paginator
from django.db import models
from .models import DepartmentAdminAssignment, Enquiry, STATUS_CHOICES
from django.utils import timezone
from datetime import datetime, timedelta
import json
import logging
import json
import logging
import logging
from django.utils import timezone
from datetime import datetime, timedelta
import json
from datetime import date, time
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
import os
import csv
from io import BytesIO  # Import for BytesIO
from reportlab.pdfgen import canvas  # Import for canvas
from reportlab.lib.pagesizes import letter  # Import for letter
import csv
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import ChatbotSettings, ChatbotQA
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import EmailMessage

from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import logging
import threading

# Set up logging


def home(request):
    return render(request, "forms/home.html")

def department_list(request):
    departments = Department.objects.all()
    return render(request, "forms/department_list.html", {"departments": departments})

def load_department_form(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    form = get_object_or_404(DynamicForm, department=department)
    dynamic_form = EnquiryForm()
    for field in form.fields.all():
        if field.field_type == 'select':
            choices = [(opt, opt) for opt in field.option_list]
            dynamic_form.fields[field.label] = forms.ChoiceField(choices=choices, required=field.required)
        elif field.field_type == 'textarea':
            dynamic_form.fields[field.label] = forms.CharField(widget=forms.Textarea, required=field.required)
        elif field.field_type == 'email':
            dynamic_form.fields[field.label] = forms.EmailField(required=field.required)
        elif field.field_type == 'number':
            dynamic_form.fields[field.label] = forms.IntegerField(required=field.required)
        elif field.field_type == 'date':
            dynamic_form.fields[field.label] = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=field.required)
        elif field.field_type == 'time':
            dynamic_form.fields[field.label] = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=field.required)
        elif field.field_type == 'password':
            dynamic_form.fields[field.label] = forms.CharField(widget=forms.PasswordInput, required=field.required)
        elif field.field_type == 'checkbox':
            choices = [(opt, opt) for opt in field.option_list]
            dynamic_form.fields[field.label] = forms.MultipleChoiceField(choices=choices, widget=forms.CheckboxSelectMultiple, required=field.required)
        elif field.field_type == 'radio':
            choices = [(opt, opt) for opt in field.option_list]
            dynamic_form.fields[field.label] = forms.ChoiceField(choices=choices, widget=forms.RadioSelect, required=field.required)
        elif field.field_type == 'file':
            dynamic_form.fields[field.label] = forms.FileField(required=field.required)
        elif field.field_type == 'range':
            dynamic_form.fields[field.label] = forms.IntegerField(widget=forms.NumberInput(attrs={'type': 'range'}), required=field.required)
        elif field.field_type == 'tel':
            dynamic_form.fields[field.label] = forms.CharField(widget=forms.TextInput(attrs={'type': 'tel'}), required=field.required)
        elif field.field_type == 'url':
            dynamic_form.fields[field.label] = forms.URLField(required=field.required)
        elif field.field_type == 'hidden':
            dynamic_form.fields[field.label] = forms.CharField(widget=forms.HiddenInput, required=field.required)
        elif field.field_type == 'color':
            dynamic_form.fields[field.label] = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=field.required)
        else:  # text, submit, reset, button
            dynamic_form.fields[field.label] = forms.CharField(required=field.required)
    return render(request, "forms/form_fields.html", {"department": department, "form_obj": dynamic_form, "form_model": form})


def send_async_email(subject, text_content, from_email, recipient_list, html_content=None):
    def _send():
        try:
            email = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
            if html_content:
                email.attach_alternative(html_content, "text/html")
            email.send()
            # Email sent successfully (no logging)
        except Exception:
            # Failed to send email (no logging)
            pass

    threading.Thread(target=_send, daemon=True).start()

@csrf_exempt
def submit_enquiry(request, form_id):
    if request.method == 'POST':
        try:
            form_model = get_object_or_404(DynamicForm, id=form_id)
          

            # Handle form-encoded data
            data = request.POST
            files = request.FILES

            # Create EnquiryForm for validation
            dynamic_form = EnquiryForm(data=data, files=files)
            for field in form_model.fields.all():
                if field.field_type == 'select':
                    choices = [(opt, opt) for opt in field.option_list]
                    dynamic_form.fields[field.label] = forms.ChoiceField(choices=choices, required=field.required)
                elif field.field_type == 'textarea':
                    dynamic_form.fields[field.label] = forms.CharField(widget=forms.Textarea, required=field.required)
                elif field.field_type == 'email':
                    dynamic_form.fields[field.label] = forms.EmailField(required=field.required)
                elif field.field_type == 'number':
                    dynamic_form.fields[field.label] = forms.IntegerField(required=field.required)
                elif field.field_type == 'date':
                    dynamic_form.fields[field.label] = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=field.required)
                elif field.field_type == 'time':
                    dynamic_form.fields[field.label] = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=field.required)
                elif field.field_type == 'password':
                    dynamic_form.fields[field.label] = forms.CharField(widget=forms.PasswordInput, required=field.required)
                elif field.field_type == 'checkbox':
                    choices = [(opt, opt) for opt in field.option_list]
                    dynamic_form.fields[field.label] = forms.MultipleChoiceField(
                        choices=choices,
                        widget=forms.CheckboxSelectMultiple,
                        required=field.required
                    )
                elif field.field_type == 'radio':
                    choices = [(opt, opt) for opt in field.option_list]
                    dynamic_form.fields[field.label] = forms.ChoiceField(choices=choices, widget=forms.RadioSelect, required=field.required)
                elif field.field_type == 'file':
                    dynamic_form.fields[field.label] = forms.FileField(required=field.required)
                    if field.max_file_size_mb:
                        max_size_bytes = field.max_file_size_mb * 1024 * 1024
                        dynamic_form.fields[field.label].validators.append(
                            lambda f: validate_file_size(f, max_size_bytes, field.label)
                        )
                elif field.field_type == 'range':
                    dynamic_form.fields[field.label] = forms.IntegerField(widget=forms.NumberInput(attrs={'type': 'range'}), required=field.required)
                elif field.field_type == 'tel':
                    dynamic_form.fields[field.label] = forms.CharField(widget=forms.TextInput(attrs={'type': 'tel'}), required=field.required)
                elif field.field_type == 'url':
                    dynamic_form.fields[field.label] = forms.URLField(required=field.required)
                elif field.field_type == 'hidden':
                    dynamic_form.fields[field.label] = forms.CharField(widget=forms.HiddenInput, required=field.required)
                elif field.field_type == 'color':
                    dynamic_form.fields[field.label] = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=field.required)
                else:
                    dynamic_form.fields[field.label] = forms.CharField(required=field.required)

            # Custom validation for required checkboxes
            for field in form_model.fields.all():
                if field.field_type == 'checkbox' and field.required:
                    if not data.getlist(field.label):
                        dynamic_form.add_error(field.label, "This field is required.")

            if dynamic_form.is_valid():
                cleaned_data = dynamic_form.cleaned_data.copy()
                user_email = None  # Initialize user_email as None
                for field in form_model.fields.all():
                    if field.field_type == 'email':  # Check for email field type
                        user_email = cleaned_data.get(field.label, '')  # Get email based on the field label
                        break  # Exit loop after finding the email field

                for key, value in cleaned_data.items():
                    if isinstance(value, date):
                        cleaned_data[key] = value.isoformat()
                    elif isinstance(value, time):
                        cleaned_data[key] = value.strftime('%H:%M:%S')
                    elif isinstance(value, (InMemoryUploadedFile, TemporaryUploadedFile)):
                        file_path = os.path.join('enquiries', form_model.name, value.name)
                        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        with open(full_path, 'wb+') as destination:
                            for chunk in value.chunks():
                                destination.write(chunk)
                        cleaned_data[key] = file_path
                    elif isinstance(value, list):
                        cleaned_data[key] = value

                enquiry = Enquiry.objects.create(form=form_model, data=cleaned_data)
                
                data_keys = list(cleaned_data.keys())
                # Dynamically determine the 'text' (name) key based on content and position
                field_mapping = {'text': None}
                remaining_keys = [k for k in data_keys if k != 'date']  # Exclude 'date' if present
                if remaining_keys:
                    field_mapping['text'] = next((k for k in remaining_keys if any(x in k.lower() for x in ['name', 'user'])), remaining_keys[0])
                user_name = str(cleaned_data.get(field_mapping['text'], 'User'))
                

                # ===================== EMAIL TO USER =====================
                if user_email:  # Check if user_email was found
                    subject = "Enquiry Confirmation"
                    text_content = f"""Hello {user_name},
                Your enquiry has been registered successfully.
                Register Number: {enquiry.register_number}
                Check your enquiry status at: {request.build_absolute_uri("/status/")}
                Department Phone: {form_model.department.dep_phone}
                Thank you,
                {form_model.department.name} Department
                """
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>Enquiry Confirmation</title>
                    </head>
                    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; line-height: 1.6;">
                        <div style="max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden;">
                            
                            <!-- Header Section -->
                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center; color: white;">
                                <h1 style="margin: 0; font-size: 28px; font-weight: 600; letter-spacing: -0.5px;">Enquiry Confirmation</h1>
                                <p style="margin: 8px 0 0 0; font-size: 16px; opacity: 0.9;">Your request has been successfully processed</p>
                            </div>
                            
                            <!-- Content Section -->
                            <div style="padding: 40px 30px;">
                                <div style="margin-bottom: 30px;">
                                    <p style="font-size: 16px; color: #374151; margin: 0 0 8px 0;">Dear <strong>{user_name}</strong>,</p>
                                    <p style="font-size: 16px; color: #6b7280; margin: 0; line-height: 1.5;">Thank you for submitting your enquiry. We have successfully registered your request and our team will review it shortly.</p>
                                </div>
                                
                                <!-- Details Card -->
                                <div style="background-color: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 25px; margin: 30px 0;">
                                    <h3 style="margin: 0 0 20px 0; font-size: 18px; color: #111827; font-weight: 600;">Enquiry Details</h3>
                                    
                                    <div style="display: table; width: 100%; border-collapse: collapse;">
                                        <div style="display: table-row;">
                                            <div style="display: table-cell; padding: 8px 0; width: 140px; font-weight: 600; color: #374151; font-size: 14px;">Registration ID:</div>
                                            <div style="display: table-cell; padding: 8px 0; color: #1f2937; font-size: 14px; font-family: 'Courier New', monospace; background-color: #e5e7eb; padding: 4px 8px; border-radius: 4px;">{enquiry.register_number}</div>
                                        </div>
                                        <div style="display: table-row;">
                                            <div style="display: table-cell; padding: 8px 0; width: 140px; font-weight: 600; color: #374151; font-size: 14px;">Department:</div>
                                            <div style="display: table-cell; padding: 8px 0; color: #1f2937; font-size: 14px;">{form_model.department.name}</div>
                                        </div>
                                        <div style="display: table-row;">
                                            <div style="display: table-cell; padding: 8px 0; width: 140px; font-weight: 600; color: #374151; font-size: 14px;">Contact Phone:</div>
                                            <div style="display: table-cell; padding: 8px 0; color: #1f2937; font-size: 14px;">{form_model.department.dep_phone}</div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Call to Action -->
                                <div style="text-align: center; margin: 35px 0;">
                                    <a href="{request.build_absolute_uri('/status/')}" 
                                    style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; letter-spacing: 0.3px; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);">
                                        Track Your Enquiry Status
                                    </a>
                                </div>
                                
                                <!-- Additional Info -->
                                <div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 20px; margin: 30px 0; border-radius: 0 8px 8px 0;">
                                    <p style="margin: 0; font-size: 14px; color: #1e40af; line-height: 1.5;">
                                        <strong>What's Next?</strong><br>
                                        Our team will review your enquiry and respond within 2-5 business hours. You can track the progress using the registration ID provided above.
                                        If you need immediate assistance, please contact us at {form_model.department.dep_phone}
                                    </p>
                                </div>
                                
                                <div style="margin-top: 40px; padding-top: 30px; border-top: 1px solid #e5e7eb;">
                                    <p style="margin: 0 0 8px 0; font-size: 16px; color: #374151;">Best regards,</p>
                                    <p style="margin: 0; font-size: 16px; font-weight: 600; color: #111827;">{form_model.department.name} Department</p>
                                </div>
                            </div>
                            
                            <!-- Footer -->
                            <div style="background-color: #f3f4f6; padding: 25px 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">
                                    This is an automated message. Please do not reply to this email.<br>
                                </p>
                            </div>
                            
                        </div>
                    </body>
                    </html>
                    """
                    try:
                        send_async_email(subject, text_content, settings.EMAIL_HOST_USER, [user_email], html_content)
                        messages.success(request, f"Queued email to User: {user_email}")
                    except Exception as e:
                        messages.error(request, f"Failed to queue user email: {str(e)}")
                else:
                    messages.error(request, "User email not found.")

                # ===================== EMAIL TO DEPARTMENT =====================
                dep_email = form_model.department.dep_email
                if dep_email:
                    subject = "New Enquiry Received"
                    text_content = f"""Hello,

                A new enquiry has been registered in your department.

                Register Number: {enquiry.register_number}
                Submitted by: {user_name}
                Check your dashboard for full details.

                Thanks,
                System
                """
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>New Enquiry Alert</title>
                    </head>
                    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; line-height: 1.6;">
                        <div style="max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden;">
                            
                            <!-- Header Section -->
                            <div style="background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); padding: 30px; text-align: center; color: white;">
                                <h1 style="margin: 0; font-size: 24px; font-weight: 600; letter-spacing: -0.3px;">New Enquiry Alert</h1>
                                <p style="margin: 8px 0 0 0; font-size: 14px; opacity: 0.9;">Immediate attention required</p>
                            </div>
                            
                            <!-- Content Section -->
                            <div style="padding: 30px;">
                                <div style="margin-bottom: 25px;">
                                    <p style="font-size: 16px; color: #374151; margin: 0 0 15px 0;">Dear Team,</p>
                                    <p style="font-size: 15px; color: #6b7280; margin: 0; line-height: 1.5;">A new enquiry has been submitted to your department and requires your attention. Please review the details below and take appropriate action.</p>
                                </div>
                                
                                <!-- Alert Box -->
                                <div style="background: linear-gradient(135deg, #fef2f2 0%, #fdf2f8 100%); border-left: 4px solid #dc2626; padding: 20px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                                    <h3 style="margin: 0 0 15px 0; font-size: 16px; color: #dc2626; font-weight: 600;">Enquiry Details</h3>
                                    
                                    <div style="display: table; width: 100%; border-collapse: collapse;">
                                        <div style="display: table-row;">
                                            <div style="display: table-cell; padding: 6px 0; width: 130px; font-weight: 600; color: #374151; font-size: 14px;">Registration ID:</div>
                                            <div style="display: table-cell; padding: 6px 0; color: #1f2937; font-size: 14px; font-family: 'Courier New', monospace; background-color: #e5e7eb; padding: 4px 8px; border-radius: 4px; display: inline-block;">{enquiry.register_number}</div>
                                        </div>
                                        <div style="display: table-row;">
                                            <div style="display: table-cell; padding: 6px 0; width: 130px; font-weight: 600; color: #374151; font-size: 14px;">Submitted By:</div>
                                            <div style="display: table-cell; padding: 6px 0; color: #1f2937; font-size: 14px; font-weight: 500;">{user_name}</div>
                                        </div>
                                        <div style="display: table-row;">
                                            <div style="display: table-cell; padding: 6px 0; width: 130px; font-weight: 600; color: #374151; font-size: 14px;">Department:</div>
                                            <div style="display: table-cell; padding: 6px 0; color: #1f2937; font-size: 14px;">{form_model.department.name}</div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Action Required Section -->
                                <div style="background-color: #f0f9ff; border: 1px solid #e0f2fe; border-radius: 8px; padding: 20px; margin: 25px 0;">
                                    <h4 style="margin: 0 0 12px 0; font-size: 16px; color: #0c4a6e; font-weight: 600;">Action Required</h4>
                                    <ul style="margin: 0; padding-left: 20px; color: #374151; font-size: 14px; line-height: 1.6;">
                                        <li>Review the complete enquiry details in your dashboard</li>
                                        <li>Update the status and respond to the enquiry</li>
                                    </ul>
                                </div>
                                
                                <!-- Call to Action -->
                                <div style="text-align: center; margin: 30px 0;">
                                    <a href="{request.build_absolute_uri('/dashboard/')}" 
                                    style="display: inline-block; background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 15px; letter-spacing: 0.3px; box-shadow: 0 4px 15px rgba(220, 38, 38, 0.3);">
                                        Access Dashboard
                                    </a>
                                </div>
                                
                                <!-- Priority Notice -->
                                <div style="background-color: #fef3c7; border: 1px solid #f59e0b; border-radius: 6px; padding: 15px; margin: 25px 0; text-align: center;">
                                    <p style="margin: 0; font-size: 14px; color: #92400e; font-weight: 500;">
                                        <strong>Priority Notice:</strong> Please respond to this enquiry within 2-3 business hours to maintain service quality standards.
                                    </p>
                                </div>
                                
                                <div style="margin-top: 30px; padding-top: 25px; border-top: 1px solid #e5e7eb;">
                                    <p style="margin: 0 0 5px 0; font-size: 14px; color: #6b7280;">Best regards,</p>
                                    <p style="margin: 0; font-size: 16px; font-weight: 600; color: #111827;">System Administrator</p>
                                    <p style="margin: 5px 0 0 0; font-size: 14px; color: #6b7280;">{form_model.department.name} Department</p>
                                </div>
                            </div>
                            
                            <!-- Footer -->
                            <div style="background-color: #f9fafb; padding: 20px 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">
                                    This is an automated system notification. Please log in to your dashboard for complete details.<br>
                                    For technical support, contact the system administrator.
                                </p>
                            </div>
                            
                        </div>
                    </body>
                    </html>
                    """

                    try:
                        send_async_email(subject, text_content, settings.EMAIL_HOST_USER, [dep_email], html_content)
                        messages.success(request, f"Queued email to department: {dep_email}")
                    except Exception as e:
                        messages.error(request, f"Failed to queue department email: {str(e)}")

                return JsonResponse({'success': True, 'redirect': '/success/'})

            else:
                errors = {}
                for field, error_list in dynamic_form.errors.items():
                    errors[field] = [str(error) for error in error_list]
                
                return JsonResponse({'success': False, 'errors': errors}, status=400)

        except json.JSONDecodeError as e:
            
            return JsonResponse({'success': False, 'errors': 'Invalid JSON data'}, status=400)
        except Exception as e:
            
            return JsonResponse({'success': False, 'errors': str(e)}, status=500)

    return JsonResponse({'success': False, 'errors': 'Invalid request method'}, status=400)


def validate_file_size(file, max_size_bytes, field_label):
    if file.size > max_size_bytes:
        raise forms.ValidationError(f"The file size for '{field_label}' exceeds the maximum limit of {max_size_bytes // (1024 * 1024)} MB.")
# ... (other views unchanged, e.g., dashboard, update_enquiry, success, etc.) ...

def success(request):
    return render(request, "forms/success.html")

def register(request):
    if request.method == 'POST':
        form = DepartmentAdminRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            DepartmentAdminAssignment.objects.create(user=user)
            return redirect('waiting')
    else:
        form = DepartmentAdminRegistrationForm()
    return render(request, "forms/register.html", {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            if user.is_superuser:
                return redirect('/admin/')
            assignment = DepartmentAdminAssignment.objects.filter(user=user, approved=True, department__isnull=False).first()
            if assignment:
                return redirect('dashboard')
            return redirect('waiting')
    return render(request, "forms/login.html")

def waiting(request):
    return render(request, "forms/waiting.html")



def chatbot_context(request):
    """Provide chatbot context globally to all templates."""
    settings = ChatbotSettings.load()
    return {
        'chatbot_is_enabled': settings.is_enabled,
        # 'chatbot_random_questions': ChatbotQA.objects.order_by('?')[:3] if settings.is_enabled else []
    }

def chatbot_interface(request):
    return render(request, 'forms/chatbot.html')


def search_questions(request):
    query = request.GET.get('q', '').strip()
    if query:
        questions = ChatbotQA.objects.filter(question__icontains=query)[:10]
    else:
        questions = []
    return render(request, 'forms/suggestions.html', {'questions': questions})

def get_answer(request, qa_id):
    qa = get_object_or_404(ChatbotQA, id=qa_id)
    return render(request, 'forms/chat_message.html', {'qa': qa})



@login_required
def dashboard(request):
    assignment = get_object_or_404(
        DepartmentAdminAssignment,
        user=request.user,
        approved=True,
        department__isnull=False
    )
    department = assignment.department
    base_qs = Enquiry.objects.filter(form__department=department).select_related('form')

    # Parameters
    section = request.GET.get('section', 'visualization')
    viz_filter = request.GET.get('viz_filter', 'all')
    filter_type = request.GET.get('filter', 'all')
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '')
    page_number = request.GET.get('page', '1')
    today = timezone.now().date()

    # Filtered QS for visualization data
    filtered_qs = base_qs
    if viz_filter == 'day':
        filtered_qs = filtered_qs.filter(created_at__date__gte=today - timedelta(days=6))
        
    elif viz_filter == 'month':
        filtered_qs = filtered_qs.filter(created_at__year=today.year, created_at__month=today.month)
       
    elif viz_filter == 'year':
        filtered_qs = filtered_qs.filter(created_at__year=today.year)
        
    else:
        filtered_qs = base_qs.filter(created_at__date__gte=today - timedelta(days=365 * 2))
        

    # Counts for summary cards
    total_count = filtered_qs.count()
    pending_count = filtered_qs.filter(status="pending").count()
    progress_count = filtered_qs.filter(status="in_progress").count()
    resolved_count = filtered_qs.filter(status="resolved").count()
    rejected_count = filtered_qs.filter(status="rejected").count()
   

    # Chart data
    chart_data = {"labels": [], "counts": []}
    if viz_filter == "day":
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            count = filtered_qs.filter(created_at__date=date).count()
            chart_data["labels"].append(date.strftime("%Y-%m-%d"))
            chart_data["counts"].append(count)
    elif viz_filter == "month":
        start_date = today.replace(day=1)
        end_date = (start_date + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        for day in range(1, end_date.day + 1):
            date = start_date.replace(day=day)
            count = filtered_qs.filter(created_at__date=date).count()
            chart_data["labels"].append(date.strftime("%Y-%m-%d"))
            chart_data["counts"].append(count)
    elif viz_filter == "year":
        for month in range(1, 13):
            count = filtered_qs.filter(
                created_at__year=today.year,
                created_at__month=month
            ).count()
            chart_data["labels"].append(datetime(today.year, month, 1).strftime("%b"))
            chart_data["counts"].append(count)
    else:  # all
        start_date = today - timedelta(days=365 * 2)
        months = []
        current_date = start_date.replace(day=1)
        while current_date <= today:
            months.append((current_date.year, current_date.month))
            next_month = current_date.month % 12 + 1
            next_year = current_date.year + (current_date.month // 12)
            current_date = current_date.replace(year=next_year, month=next_month, day=1)
        for year, month in months:
            count = base_qs.filter(
                created_at__year=year,
                created_at__month=month
            ).count()
            chart_data["labels"].append(f"{year}-{month:02d}")
            chart_data["counts"].append(count)

    # Doughnut chart (status distribution)
    doughnut_data = {
        "labels": ["Pending", "In Progress", "Resolved", "Rejected"],
        "counts": [pending_count, progress_count, resolved_count, rejected_count],
    }

    # Pie chart (enquiries by form type)
    forms = DynamicForm.objects.filter(department=department)
    pie_data = {
        "labels": [form.name for form in forms],
        "counts": [filtered_qs.filter(form=form).count() for form in forms],
    }

    # Enquiries for table
    enquiries = base_qs.order_by('-created_at')
    if section == 'enquiries':
        if filter_type == 'day':
            enquiries = enquiries.filter(created_at__date=today)
        elif filter_type == 'month':
            enquiries = enquiries.filter(created_at__year=today.year, created_at__month=today.month)
        elif filter_type == 'year':
            enquiries = enquiries.filter(created_at__year=today.year)

        if status_filter != 'all':
            enquiries = enquiries.filter(status=status_filter)

        if search_query:
            search_conditions = Q(register_number__icontains=search_query)
            for enquiry in enquiries[:10]:  # Limit to a reasonable number for efficiency
                data = enquiry.data or {}
                for key, value in data.items():
                    if isinstance(value, str) and search_query.lower() in str(value).lower():
                        search_conditions |= Q(id=enquiry.id)
            enquiries = enquiries.filter(search_conditions)

    # Pagination for enquiries
    paginator = Paginator(enquiries, 10)
    try:
        page_obj = paginator.get_page(page_number)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)

    # Create field mappings for enquiries based on form fields and data
    enquiry_field_mappings = []
    if section == 'enquiries' and page_obj:
        for enquiry in page_obj.object_list:
            # Log all available keys in enquiry.data for debugging
            data = enquiry.data or {}
            data_keys = list(data.keys())
            

            # Dynamically determine the keys based on content and position
            field_mapping = {'text': None, 'email': None, 'tel': None}
            remaining_keys = [k for k in data_keys if k != 'date']  # Exclude 'date'
            
            if remaining_keys:
                # Assign first key as 'text' (name), prioritizing keys with 'name' or 'user'
                field_mapping['text'] = next((k for k in remaining_keys if any(x in k.lower() for x in ['name', 'user'])), remaining_keys[0])
                
                # Assign key with '@' as 'email', or second key if no email
                field_mapping['email'] = next((k for k in remaining_keys if '@' in str(data.get(k, ''))), remaining_keys[1] if len(remaining_keys) > 1 else None)
                
                # Assign key with digits as 'tel' (phone), or third key if no digit match
                field_mapping['tel'] = next((k for k in remaining_keys if any(c.isdigit() for c in str(data.get(k, ''))) and k not in field_mapping.values()), remaining_keys[2] if len(remaining_keys) > 2 else None)
            
            enquiry_field_mappings.append({
                'enquiry': enquiry,
                'field_mapping': field_mapping
            })
           
    else:
        enquiry_field_mappings = []

    # For chatbot section
    qas = None
    if section == 'chatbot':
        qas = ChatbotQA.objects.filter(department=department).order_by('-id')
        paginator = Paginator(qas, 10)
        page_obj = paginator.get_page(page_number)
        if request.method == 'POST':
            question = request.POST.get('question')
            answer = request.POST.get('answer')
           
            if question and answer:
                ChatbotQA.objects.create(
                    department=department,
                    question=question,
                    answer=answer
                )
                qas = ChatbotQA.objects.filter(department=department).order_by('-id')
                paginator = Paginator(qas, 10)
                page_obj = paginator.get_page(page_number)
                return render(request, 'forms/qa_list.html', {
                    'qas': page_obj,
                    'page_obj': page_obj,
                    'search_query': search_query,
                })

    context = {
        'department': department,
        'page_obj': page_obj,
        'filter_type': filter_type,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_count': total_count,
        'pending_count': pending_count,
        'progress_count': progress_count,
        'resolved_count': resolved_count,
        'rejected_count': rejected_count,
        'chart_data': json.dumps(chart_data),
        'doughnut_data': json.dumps(doughnut_data),
        'pie_data': json.dumps(pie_data),
        'viz_filter': viz_filter,
        'qas': qas,
        'enquiry_field_mappings': enquiry_field_mappings
    }

    if request.headers.get('HX-Request'):
        
        if section == 'visualization':
            
            return render(request, 'forms/visualization.html', context)
        elif section == 'enquiries':
           
            return render(request, 'forms/enquiries.html', context)
        elif section == 'chatbot':
            if 'page' in request.GET and request.method != 'POST':
               
                return render(request, 'forms/qa_list.html', {
                    'qas': page_obj,
                    'page_obj': page_obj,
                    'search_query': search_query,
                })
           
            return render(request, 'forms/create_chatbot.html', context)

    return render(request, 'forms/dashboard.html', context)

@login_required
def edit_qa(request, qa_id):
    assignment = get_object_or_404(
        DepartmentAdminAssignment,
        user=request.user,
        approved=True,
        department__isnull=False
    )
    qa = get_object_or_404(ChatbotQA, id=qa_id, department=assignment.department)
    
    if request.method == 'POST':
        question = request.POST.get('question')
        answer = request.POST.get('answer')
       
        if question and answer:
            qa.question = question
            qa.answer = answer
            qa.save()
        page_number = request.POST.get('page', '1')
        qas = ChatbotQA.objects.filter(department=assignment.department).order_by('-id')
        paginator = Paginator(qas, 10)
        page_obj = paginator.get_page(page_number)
          
        return render(request, 'forms/qa_list.html', {
            'qas': page_obj,
            'page_obj': page_obj,
            'search_query': request.POST.get('q', '')
        })
    return render(request, 'forms/edit_qa.html', {'qa': qa})

@login_required
def delete_qa(request, qa_id):
    assignment = get_object_or_404(
        DepartmentAdminAssignment,
        user=request.user,
        approved=True,
        department__isnull=False
    )
    qa = get_object_or_404(ChatbotQA, id=qa_id, department=assignment.department)
    if request.method in ['DELETE', 'POST']:  # Support both methods
       
        qa.delete()
        page_number = request.GET.get('page', '1')
        qas = ChatbotQA.objects.filter(department=assignment.department).order_by('-id')
        paginator = Paginator(qas, 10)
        page_obj = paginator.get_page(page_number)
        
        return render(request, 'forms/qa_list.html', {
            'qas': page_obj,
            'page_obj': page_obj,
            'search_query': request.GET.get('q', '')
        })
   
    return HttpResponse(status=405)  # Method not allowed


@login_required
def delete_enquiry(request, enquiry_id):
    enquiry = get_object_or_404(Enquiry, id=enquiry_id)
    if not request.user.is_superuser:
        assignment = get_object_or_404(DepartmentAdminAssignment, user=request.user, approved=True, department__isnull=False)
        if enquiry.form.department != assignment.department:
            
            return HttpResponse("Unauthorized", status=403)
    
    if request.method == 'POST':
       
        department = enquiry.form.department
        try:
            enquiry.delete()
        except Exception as e:
          
            return HttpResponse("Error deleting enquiry", status=500)
        
        # Get query parameters
        params = {
            'q': request.POST.get('q', ''),
            'filter': request.POST.get('filter', 'all'),
            'status': request.POST.get('status', 'all'),
            'page': request.POST.get('page', '1'),
            'section': request.POST.get('section', 'enquiries'),
        }
       

        # Apply filtering logic
        enquiries = Enquiry.objects.filter(form__department=department).order_by('-created_at')
        
        # Apply search query
        if params['q']:
            enquiries = enquiries.filter(
                Q(register_number__icontains=params['q']) |
                Q(data__icontains=params['q'])
            )
        
        # Apply time filter
        if params['filter'] == 'day':
            enquiries = enquiries.filter(created_at__date=timezone.now().date())
        elif params['filter'] == 'month':
            enquiries = enquiries.filter(created_at__month=timezone.now().month, created_at__year=timezone.now().year)
        elif params['filter'] == 'year':
            enquiries = enquiries.filter(created_at__year=timezone.now().year)
        
        # Apply status filter
        if params['status'] != 'all':
            enquiries = enquiries.filter(status=params['status'])
        
        # Paginate the results
        paginator = Paginator(enquiries, 10)
        page_obj = paginator.get_page(params['page'])
        
        # Adjust page if empty (e.g., last item on page deleted)
        if not page_obj.object_list and page_obj.number > 1:
            params['page'] = str(page_obj.number - 1)
            page_obj = paginator.get_page(params['page'])
        
        # Generate enquiry_field_mappings with dynamic key detection
        enquiry_field_mappings = []
        for enquiry in page_obj.object_list:
            # Log all available keys in enquiry.data for debugging
            data = enquiry.data or {}
            data_keys = list(data.keys())
            

            # Dynamically determine the keys based on content and position
            field_mapping = {}
            remaining_keys = [k for k in data_keys if k != 'date']  # Exclude 'date'
            
            if remaining_keys:
                # Assign first key as 'text' (name), prioritizing keys with 'name' or 'user'
                field_mapping['text'] = next((k for k in remaining_keys if any(x in k.lower() for x in ['name', 'user'])), remaining_keys[0])
                
                # Assign key with '@' as 'email', or second key if no email
                field_mapping['email'] = next((k for k in remaining_keys if '@' in str(data.get(k, ''))), remaining_keys[1] if len(remaining_keys) > 1 else None)
                
                # Assign key with digits as 'tel' (phone), or third key if no digit match
                field_mapping['tel'] = next((k for k in remaining_keys if any(c.isdigit() for c in str(data.get(k, ''))) and k not in field_mapping.values()), remaining_keys[2] if len(remaining_keys) > 2 else None)
            
            enquiry_field_mappings.append({
                'enquiry': enquiry,
                'field_mapping': field_mapping
            })
           
        
        # Render the full enquiries.html template
        return render(request, 'forms/enquiries.html', {
            'department': department,
            'page_obj': page_obj,
            'enquiry_field_mappings': enquiry_field_mappings,
            'search_query': params['q'],
            'filter_type': params['filter'],
            'status_filter': params['status'],
        })
    
    return HttpResponse(status=405)


def chatbot_interface(request):
    settings = ChatbotSettings.load()
    if not settings.is_enabled:
        return HttpResponse('')
    return render(request, 'forms/chatbot.html')

def search_questions(request):
    query = request.GET.get('q', '')
    questions = ChatbotQA.objects.filter(question__icontains=query)[:10]
    return render(request, 'forms/suggestions.html', {'questions': questions})

def get_answer(request, qa_id):
    qa = get_object_or_404(ChatbotQA, id=qa_id)
    return render(request, 'forms/chat_message.html', {'qa': qa})

@login_required
def update_enquiry(request, enquiry_id):
    enquiry = get_object_or_404(Enquiry, id=enquiry_id)
    if not request.user.is_superuser:
        assignment = get_object_or_404(DepartmentAdminAssignment, user=request.user, approved=True, department__isnull=False)
        if enquiry.form.department != assignment.department:
            return HttpResponse("Unauthorized", status=403)
    if request.method == 'POST':
        try:
            # Handle form-encoded data (no JSON support for redirect approach)
            status = request.POST.get('status')
            reply = request.POST.get('reply', '')
            if status not in dict(STATUS_CHOICES).keys():
                messages.error(request, 'Invalid status selected.')
                return redirect(reverse('enquiry_detail', args=[enquiry_id]))
            enquiry.status = status
            enquiry.reply = reply
            enquiry.save()
           
            messages.success(request, 'The enquiry was updated successfully.')
            return redirect(reverse('dashboard') + '?section=enquiries')
        except Exception as e:
           
            messages.error(request, f'Error updating enquiry: {str(e)}')
            return redirect(reverse('enquiry_detail', args=[enquiry_id]))
    return HttpResponse("Invalid request method", status=400)

@login_required
def enquiry_detail(request, enquiry_id):
    enquiry = get_object_or_404(Enquiry, id=enquiry_id)
    if not request.user.is_superuser:
        assignment = get_object_or_404(DepartmentAdminAssignment, user=request.user, approved=True, department__isnull=False)
        if enquiry.form.department != assignment.department:
            return HttpResponse("Unauthorized", status=403)
    return render(request, 'forms/enquirydetail.html', {
        'enquiry': enquiry,
        'department': enquiry.form.department,
        'status_choices': STATUS_CHOICES,
        'MEDIA_URL': settings.MEDIA_URL
    })

@login_required
def export_enquiries_csv(request):
    assignment = get_object_or_404(
        DepartmentAdminAssignment,
        user=request.user,
        approved=True,
        department__isnull=False
    )
    department = assignment.department
    base_qs = Enquiry.objects.filter(form__department=department).select_related('form')

    filter_type = request.GET.get('filter', 'all')
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '')
    today = timezone.now().date()

    enquiries = base_qs.order_by('-created_at')
    if filter_type == 'day':
        enquiries = enquiries.filter(created_at__date=today)
    elif filter_type == 'month':
        enquiries = enquiries.filter(created_at__year=today.year, created_at__month=today.month)
    elif filter_type == 'year':
        enquiries = enquiries.filter(created_at__year=today.year)

    if status_filter != 'all':
        enquiries = enquiries.filter(status=status_filter)

    # Apply search query in Python if present
    if search_query:
        filtered_enquiries = []
        for enquiry in enquiries:
            data = enquiry.data or {}
            for value in data.values():
                if isinstance(value, str) and search_query.lower() in str(value).lower():
                    filtered_enquiries.append(enquiry)
                    break
        enquiries = filtered_enquiries
    else:
        enquiries = list(enquiries)  # Convert to list for consistency

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="enquiries.csv"'

    writer = csv.writer(response)
    writer.writerow(['Register No', 'Name', 'Email', 'Phone', 'Status', 'Created At'])

    for enquiry in enquiries:
        data = enquiry.data or {}
        data_keys = list(data.keys())
        # Dynamically determine the keys based on content and position
        field_mapping = {'text': None, 'email': None, 'tel': None}
        remaining_keys = [k for k in data_keys if k != 'date']  # Exclude 'date'
        
        if remaining_keys:
            # Assign first key as 'text' (name), prioritizing keys with 'name' or 'user'
            field_mapping['text'] = next((k for k in remaining_keys if any(x in k.lower() for x in ['name', 'user'])), remaining_keys[0])
            
            # Assign key with '@' as 'email', or second key if no email
            field_mapping['email'] = next((k for k in remaining_keys if '@' in str(data.get(k, ''))), remaining_keys[1] if len(remaining_keys) > 1 else None)
            
            # Assign key with digits as 'tel' (phone), or third key if no digit match
            field_mapping['tel'] = next((k for k in remaining_keys if any(c.isdigit() for c in str(data.get(k, ''))) and k not in field_mapping.values()), remaining_keys[2] if len(remaining_keys) > 2 else None)

        writer.writerow([
            enquiry.register_number,
            str(data.get(field_mapping['text'], 'N/A')),
            str(data.get(field_mapping['email'], 'N/A')),
            str(data.get(field_mapping['tel'], 'N/A')),
            enquiry.status,
            enquiry.created_at
        ])

    return response

@login_required
def export_enquiries_pdf(request):
    assignment = get_object_or_404(
        DepartmentAdminAssignment,
        user=request.user,
        approved=True,
        department__isnull=False
    )
    department = assignment.department
    base_qs = Enquiry.objects.filter(form__department=department).select_related('form')

    filter_type = request.GET.get('filter', 'all')
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '')
    today = timezone.now().date()

    enquiries = base_qs.order_by('-created_at')
    if filter_type == 'day':
        enquiries = enquiries.filter(created_at__date=today)
    elif filter_type == 'month':
        enquiries = enquiries.filter(created_at__year=today.year, created_at__month=today.month)
    elif filter_type == 'year':
        enquiries = enquiries.filter(created_at__year=today.year)

    if status_filter != 'all':
        enquiries = enquiries.filter(status=status_filter)

    # Apply search query in Python if present
    if search_query:
        filtered_enquiries = []
        for enquiry in enquiries:
            data = enquiry.data or {}
            for value in data.values():
                if isinstance(value, str) and search_query.lower() in str(value).lower():
                    filtered_enquiries.append(enquiry)
                    break
        enquiries = filtered_enquiries
    else:
        enquiries = list(enquiries)  # Convert to list for consistency

    # Prepare response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="enquiries_{department.name}.pdf"'

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=40,
        bottomMargin=40,
        leftMargin=30,
        rightMargin=30
    )
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="TitleStyle",
        fontSize=16,
        leading=22,
        alignment=1,  # Center
        spaceAfter=20,
        fontName="Helvetica-Bold"
    )
    normal_style = styles["Normal"]
    normal_style.fontSize = 9
    normal_style.leading = 12

    # Title
    elements.append(Paragraph(f"{department.name} – Enquiries Report", title_style))

    # Table headers
    table_data = [[
        Paragraph("<b>Register No</b>", normal_style),
        Paragraph("<b>Name</b>", normal_style),
        Paragraph("<b>Email</b>", normal_style),
        Paragraph("<b>Phone</b>", normal_style),
        Paragraph("<b>Status</b>", normal_style),
        Paragraph("<b>Created At</b>", normal_style)
    ]]

    # Rows
    for enquiry in enquiries:
        data = enquiry.data or {}
        data_keys = list(data.keys())
        # Dynamically determine the keys based on content and position
        field_mapping = {'text': None, 'email': None, 'tel': None}
        remaining_keys = [k for k in data_keys if k != 'date']  # Exclude 'date'
        
        if remaining_keys:
            # Assign first key as 'text' (name), prioritizing keys with 'name' or 'user'
            field_mapping['text'] = next((k for k in remaining_keys if any(x in k.lower() for x in ['name', 'user'])), remaining_keys[0])
            
            # Assign key with '@' as 'email', or second key if no email
            field_mapping['email'] = next((k for k in remaining_keys if '@' in str(data.get(k, ''))), remaining_keys[1] if len(remaining_keys) > 1 else None)
            
            # Assign key with digits as 'tel' (phone), or third key if no digit match
            field_mapping['tel'] = next((k for k in remaining_keys if any(c.isdigit() for c in str(data.get(k, ''))) and k not in field_mapping.values()), remaining_keys[2] if len(remaining_keys) > 2 else None)

        table_data.append([
            Paragraph(str(enquiry.register_number), normal_style),
            Paragraph(str(data.get(field_mapping['text'], 'N/A')), normal_style),
            Paragraph(str(data.get(field_mapping['email'], 'N/A')), normal_style),
            Paragraph(str(data.get(field_mapping['tel'], 'N/A')), normal_style),
            Paragraph(str(enquiry.status.capitalize()), normal_style),
            Paragraph(str(enquiry.created_at.strftime("%Y-%m-%d %H:%M")), normal_style),
        ])

    # Column widths (adjust so content fits nicely)
    col_widths = [80, 100, 150, 90, 70, 110]

    # Create styled table
    table = Table(table_data, colWidths=col_widths, repeatRows=1)  # repeat header on new pages
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#59a2eb")),  # header bg
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),                # header text
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))

    elements.append(table)

    # Build PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response

def status_page(request):
    return render(request, "forms/status.html")

@csrf_exempt
def check_status(request):
    if request.method == 'POST':
        reg_num = request.POST.get('reg_num')
        try:
            enquiry = Enquiry.objects.get(register_number=reg_num)
            data = enquiry.data or {}
            data_keys = list(data.keys())
            # Dynamically determine the 'text' (name) key based on content and position
            field_mapping = {'text': None}
            remaining_keys = [k for k in data_keys if k != 'date']  # Exclude 'date'
            if remaining_keys:
                field_mapping['text'] = next((k for k in remaining_keys if any(x in k.lower() for x in ['name', 'user'])), remaining_keys[0])
            name = str(data.get(field_mapping['text'], 'User'))
            return render(request, "forms/status_partial.html", {'enquiry': enquiry, 'name': name})
        except Enquiry.DoesNotExist:
            return render(request, "forms/status_partial.html", {})
    return HttpResponse("Invalid request", status=400)

@login_required
def download_pdf(request, reg_num):
    enquiry = get_object_or_404(Enquiry, register_number=reg_num)
    data = enquiry.data or {}
    data_keys = list(data.keys())
    # Dynamically determine the 'text' (name) key based on content and position
    field_mapping = {'text': None}
    remaining_keys = [k for k in data_keys if k != 'date']  # Exclude 'date'
    if remaining_keys:
        field_mapping['text'] = next((k for k in remaining_keys if any(x in k.lower() for x in ['name', 'user'])), remaining_keys[0])
    name = str(data.get(field_mapping['text'], 'User'))

    # Prepare response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="enquiry_{reg_num}.pdf"'

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=40,
        bottomMargin=40,
        leftMargin=30,
        rightMargin=30
    )
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="TitleStyle",
        fontSize=16,
        leading=22,
        alignment=1,  # Center
        spaceAfter=20,
        fontName="Helvetica-Bold"
    )
    normal_style = styles["Normal"]
    normal_style.fontSize = 9
    normal_style.leading = 12

    # Title
    elements.append(Paragraph(f"Enquiry Details - {enquiry.register_number}", title_style))

    # Table headers
    table_data = [[
        Paragraph("<b>Field</b>", normal_style),
        Paragraph("<b>Details</b>", normal_style),
    ]]

    # Rows
    table_data.extend([
        [Paragraph("Full Name", normal_style), Paragraph(str(name), normal_style)],
        [Paragraph("Register Number", normal_style), Paragraph(str(enquiry.register_number), normal_style)],
        [Paragraph("Department", normal_style), Paragraph(str(enquiry.form.department.name), normal_style)],
        [Paragraph("Form Type", normal_style), Paragraph(str(enquiry.form.name), normal_style)],
        [Paragraph("Submitted On", normal_style), Paragraph(str(enquiry.created_at.strftime("%Y-%m-%d %H:%M")), normal_style)],
        [Paragraph("Status", normal_style), Paragraph(str(enquiry.get_status_display()), normal_style)],
        [Paragraph("Official Response", normal_style), Paragraph(str(enquiry.reply if enquiry.reply else "Awaiting Response"), normal_style)],
    ])

    # Column widths
    col_widths = [150, 350]

    # Create styled table
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#59a2eb")),  # header bg
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),                # header text
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))

    elements.append(table)

    # Build PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response
def custom_logout(request):
    logout(request)
    return redirect('home')

