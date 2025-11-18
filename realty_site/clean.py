import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realty_site.settings')
django.setup()

from realty.models import Message

def cleanup_old_messages():
    # Удаляем сообщения без диалогов
    count, _ = Message.objects.filter(dialogue__isnull=True).delete()
    print(f"Удалено {count} старых сообщений без диалогов")

if __name__ == '__main__':
    cleanup_old_messages()