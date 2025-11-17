from django.contrib.auth.models import AbstractUser
from django.db import models
import re
from django.core.exceptions import ValidationError


class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('realtor', 'Риэлтор'),
        ('client', 'Клиент'),
    )
    GENDER_CHOICES = (
        ('M', 'Мужской'),
        ('F', 'Женский'),
    )

    user_type = models.CharField('Тип пользователя', max_length=10, choices=USER_TYPE_CHOICES)
    phone = models.CharField('Телефон', max_length=20, blank=True)
    bio = models.TextField('О себе', blank=True)
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True, null=True)
    gender = models.CharField('Пол', max_length=1, choices=GENDER_CHOICES, blank=True)

    def clean(self):
        if self.password and len(self.password) < 5:
            raise ValidationError("Пароль должен содержать не менее 5 символов")
        if self.password and (not re.search(r'[A-Za-z]', self.password) or not re.search(r'[0-9]', self.password)):
            raise ValidationError("Пароль должен содержать как буквы, так и цифры")

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


class Blacklist(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='blacklist_owner')
    blocked_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='blocked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'blocked_user')

    def __str__(self):
        return f"{self.user} блокировал {self.blocked_user}"


class Property(models.Model):
    STATUS_CHOICES = (
        ('active', 'Актуально'),
        ('sold', 'Продано'),
        ('hidden', 'Скрыто'),
    )

    PROPERTY_TYPES = (
        ('apartment', 'Квартира'),
        ('house', 'Дом'),
        ('land', 'Земельный участок'),
        ('commercial', 'Коммерческая недвижимость'),
    )

    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание')
    price = models.DecimalField('Цена', max_digits=12, decimal_places=2)
    property_type = models.CharField('Тип недвижимости', max_length=20, choices=PROPERTY_TYPES)
    area = models.FloatField('Площадь (кв.м)')
    rooms = models.IntegerField('Количество комнат', blank=True, null=True)
    location = models.CharField('Местоположение', max_length=300)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='properties')
    status = models.CharField('Статус', max_length=10, choices=STATUS_CHOICES, default='active')
    views = models.IntegerField('Просмотры', default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Объект недвижимости'
        verbose_name_plural = 'Объекты недвижимости'
        ordering = ['-created_at']


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField('Изображение', upload_to='property_images/')
    is_main = models.BooleanField('Основное изображение', default=False)

    def __str__(self):
        return f"Изображение для {self.property.title}"


class Comment(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.TextField('Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Комментарий от {self.author.username}"


class Message(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField('Тема', max_length=200)
    content = models.TextField('Содержание')
    is_read = models.BooleanField('Прочитано', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Сообщение от {self.sender.username} к {self.receiver.username}"