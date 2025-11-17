from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),

    # Аутентификация
    path('login/', auth_views.LoginView.as_view(template_name='realty/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),  # Используем кастомный выход
    path('register/', views.register, name='register'),

    # Профиль
    path('profile/', views.profile_update, name='profile'),

    # Недвижимость
    path('properties/', views.property_list, name='property_list'),
    path('property/<int:pk>/', views.property_detail, name='property_detail'),
    path('property/create/', views.property_create, name='property_create'),
    path('property/<int:pk>/edit/', views.property_edit, name='property_edit'),

    # Сообщения
    path('messages/', views.message_list, name='message_list'),
    path('messages/send/', views.message_send, name='message_send'),
    path('messages/<int:pk>/', views.message_detail, name='message_detail'),

    # Черный список
    path('blacklist/add/<int:user_id>/', views.blacklist_add, name='blacklist_add'),
]