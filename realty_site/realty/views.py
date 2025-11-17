import json
import random
import string
from django.shortcuts import render
from django.contrib.auth import login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import CustomUserCreationForm


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
            from .models import CustomUser
            username = request.GET.get('check_username')
            exists = CustomUser.objects.filter(username=username).exists()
            return JsonResponse({'exists': exists})

        # Проверка email
        if 'check_email' in request.GET:
            from .models import CustomUser
            email = request.GET.get('check_email')
            exists = CustomUser.objects.filter(email=email).exists()
            return JsonResponse({'exists': exists})

        # Обновление капчи
        if 'refresh_captcha' in request.GET:
            captcha_text = generate_captcha()
            request.session['captcha_answer'] = captcha_text
            return JsonResponse({'captcha_text': captcha_text})

        # Обычный GET - показать форму
        captcha_text = generate_captcha()
        request.session['captcha_answer'] = captcha_text
        return render(request, 'realty/register.html', {'captcha_text': captcha_text})

    # POST запрос - обработка регистрации
    if request.method == 'POST':
        # Получаем данные
        try:
            data = json.loads(request.body.decode('utf-8'))
        except:
            data = request.POST

        # Проверяем капчу
        user_captcha = data.get('captcha', '').upper()
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

            return JsonResponse({'success': True})
        else:
            # Возвращаем ошибки
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [{'message': error} for error in error_list]
            return JsonResponse({'success': False, 'errors': errors})

    return JsonResponse({'success': False, 'errors': {'__all__': [{'message': 'Неизвестная ошибка'}]}})
def home(request):
    properties = Property.objects.filter(status='active')[:6]
    return render(request, 'realty/home.html', {
        'properties': properties
    })


def property_list(request):
    """Список объектов недвижимости с фильтрацией"""
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
    paginator = Paginator(properties, 12)  # 12 объектов на страницу
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
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.created_by = request.user
            property_obj.save()

            # Обработка изображений
            images = request.FILES.getlist('images')
            for i, image in enumerate(images):
                PropertyImage.objects.create(
                    property=property_obj,
                    image=image,
                    is_main=(i == 0)  # Первое изображение - основное
                )

            return redirect('property_detail', pk=property_obj.pk)
    else:
        form = PropertyForm()

    return render(request, 'realty/property_form.html', {'form': form})


@login_required
def property_edit(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, created_by=request.user)

    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property_obj)
        if form.is_valid():
            form.save()

            # Обновление изображений
            new_images = request.FILES.getlist('images')
            for image in new_images:
                PropertyImage.objects.create(property=property_obj, image=image)

            return redirect('property_detail', pk=pk)
    else:
        form = PropertyForm(instance=property_obj)

    return render(request, 'realty/property_form.html', {'form': form, 'edit': True})


@csrf_exempt
def register(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        form = CustomUserCreationForm(data)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})

    return render(request, 'realty/register.html')


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)

    user_properties = Property.objects.filter(created_by=request.user)
    return render(request, 'realty/profile.html', {
        'form': form,
        'properties': user_properties
    })


@login_required
def message_list(request):
    messages = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by('-created_at')
    return render(request, 'realty/messages.html', {'messages': messages})


@login_required
def message_send(request):
    if request.method == 'POST':
        form = MessageForm(request.POST, sender=request.user)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})

    form = MessageForm(sender=request.user)
    return render(request, 'realty/message_send.html', {'form': form})


@login_required
def message_detail(request, pk):
    message = get_object_or_404(Message, pk=pk)

    if message.receiver == request.user and not message.is_read:
        message.is_read = True
        message.save()

    return render(request, 'realty/message_detail.html', {'message': message})


@login_required
def blacklist_add(request, user_id):
    user_to_block = get_object_or_404(CustomUser, id=user_id)

    if user_to_block != request.user:
        Blacklist.objects.get_or_create(user=request.user, blocked_user=user_to_block)
        Message.objects.filter(sender=user_to_block, receiver=request.user).delete()

    return redirect('profile')


def about(request):
    return render(request, 'realty/about.html')


@login_required
def profile_update(request):
    """Обновление профиля пользователя"""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('profile')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = ProfileUpdateForm(instance=request.user)

    user_properties = Property.objects.filter(created_by=request.user)
    return render(request, 'realty/profile.html', {
        'form': form,
        'properties': user_properties
    })


@login_required
def property_edit(request, pk):
    """Редактирование объекта недвижимости"""
    property_obj = get_object_or_404(Property, pk=pk, created_by=request.user)

    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property_obj)
        if form.is_valid():
            form.save()

            # Обновление изображений
            new_images = request.FILES.getlist('images')
            for image in new_images:
                PropertyImage.objects.create(property=property_obj, image=image)

            return redirect('property_detail', pk=pk)
    else:
        form = PropertyForm(instance=property_obj)

    return render(request, 'realty/property_form.html', {'form': form, 'edit': True, 'object': property_obj})