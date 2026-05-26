from django import forms
from django.contrib.auth.models import User
from .models import Habit
import re
from django.core.exceptions import ValidationError

# ==========================================
# AUTHENTICATION FORMS
# ==========================================

class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create a password'})
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'}), 
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password'] 
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password') != cleaned_data.get('password_confirm'):
            self.add_error('password_confirm', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        
        if password:
            # 1. Check for at least one number
            if not re.search(r'\d', password):
                raise ValidationError("Password must contain at least one number.")
            
            # 2. Check for at least one special character
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                raise ValidationError("Password must contain at least one special character.")
            
            # 3. Optional: Enforce a minimum length (e.g., 8 characters)
            if len(password) < 8:
                raise ValidationError("Password must be at least 8 characters long.")
                
        return password
class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

# ==========================================
# HABIT FORM
# ==========================================

class HabitForm(forms.ModelForm):
    name = forms.CharField(
        max_length=100, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Drink 8 glasses of water'})
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Optional: Describe your habit goal', 'rows': 3})
    )

    custom_category = forms.CharField(
        required=False, label='', 
        widget=forms.TextInput(attrs={
            'class': 'form-control mt-2',
            'placeholder': 'Type your new category here...',
            'id': 'customCategoryInput',
            'style': 'display: none;' 
        })
    )
    
    class Meta:
        model = Habit
        fields = ['name', 'description', 'category']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(HabitForm, self).__init__(*args, **kwargs)
        
        choices = [
            ('Health', 'Health'),
            ('Productivity', 'Productivity'),
            ('Learning', 'Learning'),
            ('Mindfulness', 'Mindfulness'),
            ('Social', 'Social'),
        ]
        
        existing_choice_keys = [c[0].lower() for c in choices]
        
        if user:
            existing_cats = Habit.objects.filter(user=user).values_list('category', flat=True).distinct()
            for cat in existing_cats:
                if cat:
                    clean_cat = cat.strip().title() 
                    if clean_cat.lower() not in existing_choice_keys and clean_cat.lower() != 'other':
                        choices.append((clean_cat, clean_cat))
                        existing_choice_keys.append(clean_cat.lower())
                        
        choices.append(('Other', 'Other...'))
        
        self.fields['category'] = forms.ChoiceField(
            choices=choices, 
            widget=forms.Select(attrs={'class': 'form-select', 'id': 'categorySelect'})
        )

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        custom = cleaned_data.get('custom_category')

        if category == 'Other':
            if not custom:
                self.add_error('custom_category', 'Please provide a custom category name.')
            else:
                cleaned_data['category'] = custom.strip().title()
                
        return cleaned_data