from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),

    # Аутентификация
    path('login/', auth_views.LoginView.as_view(template_name='realty/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),

    # Профиль
    path('profile/', views.profile_update, name='profile'),

    # Недвижимость
    path('properties/', views.property_list, name='property_list'),
    path('property/<int:pk>/', views.property_detail, name='property_detail'),
    path('property/create/', views.property_create, name='property_create'),
    path('property/<int:pk>/edit/', views.property_edit, name='property_edit'),

    # Управление объектами
    path('property/<int:pk>/sold/', views.property_mark_sold, name='property_mark_sold'),
    path('property/<int:pk>/hide/', views.property_hide, name='property_hide'),
    path('property/<int:pk>/activate/', views.property_reactivate, name='property_reactivate'),
    path('property/<int:pk>/delete/', views.property_delete, name='property_delete'),

    # Управление изображениями
    path('property/image/<int:image_id>/delete/', views.delete_property_image, name='delete_property_image'),
    path('property/image/<int:image_id>/set_main/', views.set_main_image, name='set_main_image'),

    # Сообщения
    path('messages/', views.message_list, name='message_list'),
    path('messages/send/', views.send_message, name='send_message'),
    path('messages/send/<int:user_id>/', views.send_message, name='message_send_to'),  # 👈 ДОБАВЬТЕ ЭТУ СТРОКУ
    path('messages/chat/<int:user_id>/', views.chat_with_user, name='chat_with_user'),

    # Черный список
    path('blacklist/add/<int:user_id>/', views.blacklist_add, name='blacklist_add'),
]