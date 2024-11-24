from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Quiz, Question, Category, Answer
from django.forms import modelformset_factory

class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label='First Name')
    last_name = forms.CharField(max_length=30, required=True, label='Last Name')
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['first_name','last_name','username', 'email', 'password1', 'password2']

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class QuizForm(forms.ModelForm):
    new_category = forms.CharField(
        required=False,
        label="Or Create New Category",
        widget=forms.TextInput(attrs={"placeholder": "Enter new category"})
    )

    class Meta:
        model = Quiz
        fields = ['name', 'description', 'category']
        labels = {
            'category': 'Select Existing Category',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add placeholder option for category dropdown
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = "Select a category..."

    def save(self, commit=True):
        # Handle new category creation
        new_category_name = self.cleaned_data.get('new_category')
        if new_category_name:
            category, created = Category.objects.get_or_create(name=new_category_name)
            self.instance.category = category
        return super().save(commit)

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type']

        # Override to customize the label
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].label = "Question"
        self.fields['question_type'].label = "Question Type"

class MultipleChoiceAnswerForm(forms.Form):
    option_1 = forms.CharField(label="Option 1", max_length=255)
    option_2 = forms.CharField(label="Option 2", max_length=255)
    option_3 = forms.CharField(label="Option 3", max_length=255)
    option_4 = forms.CharField(label="Option 4", max_length=255)
    correct_option = forms.ChoiceField(
        choices=[('1', 'Option 1'), ('2', 'Option 2'), ('3', 'Option 3'), ('4', 'Option 4')],
        label="Correct Option"
    )

class TrueFalseAnswerForm(forms.Form):
    correct_option = forms.ChoiceField(
        choices=[('True', 'True'), ('False', 'False')],
        label="Correct Answer"
    )

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        labels = {'name': 'New Category Name'}
