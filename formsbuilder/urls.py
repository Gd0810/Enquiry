from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("forms/", views.department_list, name="department_list"),
    path('department/<int:department_id>/form/', views.load_department_form, name='load_department_form'),
    path('submit-enquiry/<int:form_id>/', views.submit_enquiry, name='submit_enquiry'),
    path('success/', views.success, name='success'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('waiting/', views.waiting, name='waiting'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('chatbot/', views.chatbot_interface, name='chatbot_interface'),
    path('search-questions/', views.search_questions, name='search_questions'),
    path('get-answer/<int:qa_id>/', views.get_answer, name='get_answer'),
    path('edit-qa/<int:qa_id>/', views.edit_qa, name='edit_qa'),
    path('delete-qa/<int:qa_id>/', views.delete_qa, name='delete_qa'),
    path('export_enquiries_csv/', views.export_enquiries_csv, name='export_enquiries_csv'),
    path('export_enquiries_pdf/', views.export_enquiries_pdf, name='export_enquiries_pdf'),
    path('update-enquiry/<int:enquiry_id>/', views.update_enquiry, name='update_enquiry'),
    path('enquiry/<int:enquiry_id>/', views.enquiry_detail, name='enquiry_detail'),
    path('delete-enquiry/<int:enquiry_id>/', views.delete_enquiry, name='delete_enquiry'),
    path('status/', views.status_page, name='status'),
    path('download_pdf/<str:reg_num>/', views.download_pdf, name='download_pdf'),
    path('check-status/', views.check_status, name='check_status'),
]