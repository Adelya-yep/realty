from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Property, PropertyImage, Comment, Message, Blacklist

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('user_type', 'phone', 'bio', 'avatar', 'gender')
        }),
    )

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'property_type', 'status', 'created_by', 'created_at')
    list_filter = ('property_type', 'status', 'created_at')
    search_fields = ('title', 'description', 'location')
    inlines = [PropertyImageInline]

admin.site.register(PropertyImage)
admin.site.register(Comment)
admin.site.register(Message)
admin.site.register(Blacklist)