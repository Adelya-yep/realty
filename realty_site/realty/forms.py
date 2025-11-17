from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
import re
from .models import CustomUser, Property, Comment, Message, Blacklist, PropertyImage


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(max_length=30, required=True, label='Имя')
    last_name = forms.CharField(max_length=30, required=True, label='Фамилия')
    phone = forms.CharField(max_length=20, required=False, label='Телефон')
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False, label='О себе')
    gender = forms.ChoiceField(choices=CustomUser.GENDER_CHOICES, required=False, label='Пол')

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'user_type',
                  'gender', 'phone', 'bio', 'password1', 'password2')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError("Этот логин уже занят")
        if len(username) < 3:
            raise ValidationError("Логин должен содержать не менее 3 символов")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Этот email уже используется")
        return email

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if len(password1) < 5:
            raise ValidationError("Пароль должен содержать не менее 5 символов")
        if not re.search(r'[A-Za-z]', password1) or not re.search(r'[0-9]', password1):
            raise ValidationError("Пароль должен содержать как буквы, так и цифры")
        return password1

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not re.match(r'^[\d\s\-\+\(\)]+$', phone):
            raise ValidationError("Введите корректный номер телефона")
        return phone


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone', 'bio', 'avatar', 'gender')


class PropertyForm(forms.ModelForm):
    # Убираем множественную загрузку из формы, будем обрабатывать в view
    class Meta:
        model = Property
        fields = ('title', 'description', 'price', 'property_type',
                  'area', 'rooms', 'location', 'status')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


# Отдельная форма для загрузки изображений
class PropertyImageForm(forms.ModelForm):
    class Meta:
        model = PropertyImage
        fields = ('image',)


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Оставьте ваш комментарий...'}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('receiver', 'subject', 'content')
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.sender = kwargs.pop('sender', None)
        super().__init__(*args, **kwargs)
        if self.sender:
            blocked_users = Blacklist.objects.filter(user=self.sender).values_list('blocked_user', flat=True)
            self.fields['receiver'].queryset = CustomUser.objects.exclude(
                id__in=blocked_users
            ).exclude(id=self.sender.id)

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(max_length=30, required=True, label='Имя')
    last_name = forms.CharField(max_length=30, required=True, label='Фамилия')
    phone = forms.CharField(max_length=20, required=False, label='Телефон')
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False, label='О себе')
    gender = forms.ChoiceField(choices=CustomUser.GENDER_CHOICES, required=False, label='Пол')
    captcha = forms.CharField(max_length=10, required=True, label='Код с картинки')

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'user_type',
                  'gender', 'phone', 'bio', 'password1', 'password2', 'captcha')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['captcha'].required = True

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError("Этот логин уже занят")
        if len(username) < 3:
            raise ValidationError("Логин должен содержать не менее 3 символов")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Этот email уже используется")
        return email

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if len(password1) < 5:
            raise ValidationError("Пароль должен содержать не менее 5 символов")
        if not re.search(r'[A-Za-z]', password1) or not re.search(r'[0-9]', password1):
            raise ValidationError("Пароль должен содержать как буквы, так и цифры")
        return password1

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not re.match(r'^[\d\s\-\+\(\)]+$', phone):
            raise ValidationError("Введите корректный номер телефона")
        return phone