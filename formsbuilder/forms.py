from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class DepartmentAdminRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(DepartmentAdminRegistrationForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full bg-black/50 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none input-glow focus:border-red-500 transition-all duration-300'
            })

class EnquiryForm(forms.Form):
    # Dynamic fields added in view
    pass