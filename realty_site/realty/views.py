import json
import random
import string
from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from .models import CustomUser, Property, Comment, Message, Blacklist, PropertyImage
from .forms import CustomUserCreationForm, ProfileUpdateForm, PropertyForm, CommentForm, MessageForm


def generate_captcha():
    """Генерация простой текстовой капчи"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(6))


@csrf_exempt
def register(request):
    """Регистрация пользователя"""

    # GET запросы
    if request.method == 'GET':
        # Проверка логина
        if 'check_username' in request.GET:
            username = request.GET.get('check_username')
            exists = CustomUser.objects.filter(username=username).exists()
            return JsonResponse({'exists': exists})

        # Проверка email
        if 'check_email' in request.GET:
            email = request.GET.get('check_email')
            exists = CustomUser.objects.filter(email=email).exists()
            return JsonResponse({'exists': exists})

        # Обновление капчи
        if 'refresh_captcha' in request.GET:
            captcha_text = generate_captcha()
            request.session['captcha_answer'] = captcha_text
            request.session.modified = True
            return JsonResponse({'captcha_text': captcha_text})

        # Обычный GET - показать форму
        captcha_text = generate_captcha()
        request.session['captcha_answer'] = captcha_text
        request.session.modified = True

        return render(request, 'realty/register.html', {
            'captcha_text': captcha_text
        })

    # POST запрос - обработка регистрации
    if request.method == 'POST':
        # Получаем данные
        try:
            data = json.loads(request.body.decode('utf-8'))
        except:
            data = request.POST.dict()

        # Проверяем капчу
        user_captcha = data.get('captcha', '').strip().upper()
        correct_captcha = request.session.get('captcha_answer', '').upper()

        if user_captcha != correct_captcha:
            return JsonResponse({
                'success': False,
                'errors': {'captcha': [{'message': 'Неверный код проверки'}]}
            })

        # Создаем форму
        form = CustomUserCreationForm(data)

        if form.is_valid():
            # Сохраняем пользователя
            user = form.save()

            # Логиним пользователя
            login(request, user)

            # Очищаем капчу
            if 'captcha_answer' in request.session:
                del request.session['captcha_answer']
                request.session.modified = True

            return JsonResponse({'success': True})
        else:
            # Возвращаем ошибки
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [{'message': error} for error in error_list]
            return JsonResponse({'success': False, 'errors': errors})

    return JsonResponse({'success': False, 'errors': {'__all__': [{'message': 'Неизвестная ошибка'}]}})
# Остальные функции views (добавляем их обратно)
def home(request):
    """Главная страница с статистикой"""
    properties = Property.objects.filter(status='active')[:6]

    # Статистика для главной страницы
    properties_count = Property.objects.filter(status='active').count()
    users_count = CustomUser.objects.count()
    realtors_count = CustomUser.objects.filter(user_type='realtor').count()
    sold_count = Property.objects.filter(status='sold').count()

    return render(request, 'realty/home.html', {
        'properties': properties,
        'properties_count': properties_count,
        'users_count': users_count,
        'realtors_count': realtors_count,
        'sold_count': sold_count,
    })


def property_list(request):
    properties = Property.objects.filter(status='active')

    # Фильтрация
    property_type = request.GET.get('type')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    search = request.GET.get('search')
    rooms = request.GET.get('rooms')

    if property_type:
        properties = properties.filter(property_type=property_type)
    if min_price:
        properties = properties.filter(price__gte=min_price)
    if max_price:
        properties = properties.filter(price__lte=max_price)
    if search:
        properties = properties.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(location__icontains=search)
        )
    if rooms:
        properties = properties.filter(rooms=rooms)

    # Сортировка
    sort = request.GET.get('sort', '-created_at')
    if sort in ['price', '-price', 'created_at', '-created_at', 'views', '-views']:
        properties = properties.order_by(sort)

    # Пагинация
    paginator = Paginator(properties, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # AJAX запрос для фильтрации
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        properties_data = []
        for prop in page_obj:
            main_image = prop.images.filter(is_main=True).first()
            properties_data.append({
                'id': prop.id,
                'title': prop.title,
                'price': '{:,.0f}'.format(prop.price).replace(',', ' '),
                'location': prop.location,
                'property_type': prop.get_property_type_display(),
                'area': prop.area,
                'rooms': prop.rooms,
                'views': prop.views,
                'image_url': main_image.image.url if main_image else '/static/images/no-image.jpg',
            })
        return JsonResponse({
            'properties': properties_data,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
        })

    context = {
        'page_obj': page_obj,
        'property_types': Property.PROPERTY_TYPES,
    }
    return render(request, 'realty/property_list.html', context)


def property_detail(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)
    property_obj.views += 1
    property_obj.save()

    comments = property_obj.comments.all()

    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.property = property_obj
            comment.author = request.user
            comment.save()
            return redirect('property_detail', pk=pk)
    else:
        comment_form = CommentForm()

    return render(request, 'realty/property_detail.html', {
        'property': property_obj,
        'comments': comments,
        'comment_form': comment_form,
    })


@login_required
def property_create(request):
    """Создание нового объекта недвижимости"""
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.created_by = request.user
            property_obj.save()

            # Обработка изображений
            images = request.FILES.getlist('images')
            print(f"🔍 DEBUG: Получено файлов: {len(images)}")  # Для отладки

            for i, image in enumerate(images):
                print(f"🔍 DEBUG: Обработка файла: {image.name}")  # Для отладки
                PropertyImage.objects.create(
                    property=property_obj,
                    image=image,
                    is_main=(i == 0)  # Первое изображение - основное
                )

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'redirect_url': f'/property/{property_obj.pk}/'
                })
            return redirect('property_detail', pk=property_obj.pk)
        else:
            print(f"🔍 DEBUG: Ошибки формы: {form.errors}")  # Для отладки
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [{'message': error} for error in error_list]
                return JsonResponse({'success': False, 'errors': errors})

    form = PropertyForm()
    return render(request, 'realty/property_form.html', {'form': form})


@login_required
def property_edit(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, created_by=request.user)

    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, instance=property_obj)  # Добавьте request.FILES
        if form.is_valid():
            property_obj = form.save()

            # Обработка новых изображений
            new_images = request.FILES.getlist('images')
            for image in new_images:
                PropertyImage.objects.create(property=property_obj, image=image)

            return redirect('property_detail', pk=property_obj.pk)
    else:
        form = PropertyForm(instance=property_obj)

    return render(request, 'realty/property_form.html', {
        'form': form,
        'edit': True,
        'property': property_obj
    })
@login_required
def profile_update(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('profile')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [{'message': error} for error in error_list]
                return JsonResponse({'success': False, 'errors': errors})
    else:
        form = ProfileUpdateForm(instance=request.user)

    user_properties = Property.objects.filter(created_by=request.user)
    return render(request, 'realty/profile.html', {
        'form': form,
        'properties': user_properties
    })


@login_required
def message_list(request):
    """Простой список сообщений - последние диалоги"""
    # Получаем последнее сообщение с каждым пользователем
    sent_messages = Message.objects.filter(sender=request.user)
    received_messages = Message.objects.filter(receiver=request.user)

    # Собираем уникальных собеседников
    users = set()
    for msg in sent_messages:
        users.add(msg.receiver)
    for msg in received_messages:
        users.add(msg.sender)

    # Для каждого пользователя находим последнее сообщение
    dialogues = []
    for user in users:
        last_msg = Message.objects.filter(
            Q(sender=request.user, receiver=user) | Q(sender=user, receiver=request.user)
        ).order_by('-created_at').first()

        unread_count = Message.objects.filter(sender=user, receiver=request.user, is_read=False).count()

        dialogues.append({
            'user': user,
            'last_message': last_msg,
            'unread_count': unread_count
        })

    # Сортируем по времени последнего сообщения
    dialogues.sort(key=lambda x: x['last_message'].created_at if x['last_message'] else datetime.min, reverse=True)

    return render(request, 'realty/messages.html', {'dialogues': dialogues})


@login_required
def chat_with_user(request, user_id):
    """Чат с конкретным пользователем"""
    # Очищаем системные сообщения при входе в чат
    from django.contrib import messages as message_framework  # 👈 Переименовываем импорт
    storage = message_framework.get_messages(request)
    for message in storage:
        pass  # Просто читаем все сообщения чтобы очистить

    other_user = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                sender=request.user,
                receiver=other_user,
                content=content
            )
            return redirect('chat_with_user', user_id=user_id)

    # Получаем все сообщения между пользователями
    messages_list = Message.objects.filter(  # 👈 Переименовываем переменную
        Q(sender=request.user, receiver=other_user) | Q(sender=other_user, receiver=request.user)
    ).order_by('created_at')

    # Помечаем сообщения как прочитанные
    Message.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)

    return render(request, 'realty/chat.html', {
        'other_user': other_user,
        'messages': messages_list  # 👈 Теперь передаем messages_list
    })


@login_required
def send_message(request, user_id=None):
    """Отправить сообщение - простая форма"""
    if user_id:
        other_user = get_object_or_404(CustomUser, id=user_id)

        if request.method == 'POST':
            content = request.POST.get('content', '').strip()
            if content:
                Message.objects.create(
                    sender=request.user,
                    receiver=other_user,
                    content=content
                )
                return redirect('chat_with_user', user_id=user_id)

        return render(request, 'realty/send_message.html', {'other_user': other_user})

    # Если user_id не передан - показать выбор пользователя
    users = CustomUser.objects.exclude(id=request.user.id)
    return render(request, 'realty/choose_user.html', {'users': users})

@login_required
def blacklist_add(request, user_id):
    user_to_block = get_object_or_404(CustomUser, id=user_id)

    if user_to_block != request.user:
        Blacklist.objects.get_or_create(user=request.user, blocked_user=user_to_block)
        Message.objects.filter(sender=user_to_block, receiver=request.user).delete()

    return redirect('profile')


def about(request):
    return render(request, 'realty/about.html')

from django.contrib.auth import logout
from django.http import JsonResponse

def custom_logout(request):
    """Кастомный выход из системы с поддержкой AJAX"""
    if request.method == 'POST':
        logout(request)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('home')
    # Для GET запросов перенаправляем на домашнюю страницу
    return redirect('home')

@login_required
def property_mark_sold(request, pk):
    """Пометить объект как проданный"""
    property_obj = get_object_or_404(Property, pk=pk, created_by=request.user)
    property_obj.status = 'sold'
    property_obj.save()
    messages.success(request, f'Объект "{property_obj.title}" помечен как проданный')
    return redirect('profile')

@login_required
def property_hide(request, pk):
    """Скрыть объект"""
    property_obj = get_object_or_404(Property, pk=pk, created_by=request.user)
    property_obj.status = 'hidden'
    property_obj.save()
    messages.success(request, f'Объект "{property_obj.title}" скрыт')
    return redirect('profile')

@login_required
def property_reactivate(request, pk):
    """Вернуть объект в активные"""
    property_obj = get_object_or_404(Property, pk=pk, created_by=request.user)
    property_obj.status = 'active'
    property_obj.save()
    messages.success(request, f'Объект "{property_obj.title}" активирован')
    return redirect('profile')

@login_required
def property_delete(request, pk):
    """Удалить объект"""
    property_obj = get_object_or_404(Property, pk=pk, created_by=request.user)
    property_obj.delete()
    messages.success(request, f'Объект "{property_obj.title}" удален')
    return redirect('profile')