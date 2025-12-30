from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponseForbidden, JsonResponse
from django.contrib import messages
from .models import Article, Course, Lesson, Plan, ShopItem, PaymentHistory, CourseProgress, Comment
from .forms import CommentForm

def check_plan_access(user, required_plan):
    if not required_plan:
        return True
    
    # Allow access if the plan level is 0 (Free/Public)
    if required_plan.level == 0:
        return True
        
    if not user.is_authenticated:
        return False
    if not hasattr(user, 'profile') or not user.profile.current_plan:
        return False
    return user.profile.current_plan.level >= required_plan.level

def home(request):
    latest_articles = Article.objects.filter(status='published').order_by('-created_at')[:3]
    return render(request, 'core/index.html', {'latest_articles': latest_articles})

def content_list(request):
    category = request.GET.get('category')
    query = request.GET.get('q')
    articles = Article.objects.filter(status='published')
    courses = Course.objects.filter(status='published')
    
    if category:
        articles = articles.filter(category=category)
    
    if query:
        articles = articles.filter(title__icontains=query) | articles.filter(summary__icontains=query) | articles.filter(content__icontains=query)
        courses = courses.filter(title__icontains=query)
        
    return render(request, 'core/content_list.html', {
        'articles': articles.distinct(), 
        'current_category': category,
        'query': query
    })

def course_list(request):
    courses = Course.objects.filter(status='published')
    return render(request, 'core/course_list.html', {'courses': courses})

def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, status='published')
    
    if not check_plan_access(request.user, article.required_plan):
        if not request.user.is_authenticated:
            return redirect('account_login')
        messages.warning(request, 'Este conteúdo requer um plano superior.')
        return redirect('subscribe')
    
    comments = article.comments.filter(active=True)
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('account_login')
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.article = article
            comment.save()
            messages.success(request, 'Comentário enviado com sucesso!')
            return redirect('article_detail', slug=slug)
    else:
        form = CommentForm()
        
    return render(request, 'core/article_detail.html', {
        'article': article,
        'comments': comments,
        'comment_form': form
    })

def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug, status='published')
    return render(request, 'core/course_detail.html', {'course': course})

def lesson_detail(request, course_slug, lesson_id):
    course = get_object_or_404(Course, slug=course_slug, status='published')
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
    comments = lesson.comments.filter(active=True)
    
    is_completed = False
    if request.user.is_authenticated:
        is_completed = CourseProgress.objects.filter(user=request.user, lesson=lesson).exists()
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('account_login')
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.lesson = lesson
            comment.save()
            messages.success(request, 'Comentário enviado com sucesso!')
            return redirect('lesson_detail', course_slug=course_slug, lesson_id=lesson_id)
    else:
        form = CommentForm()

    return render(request, 'core/lesson_detail.html', {
        'course': course, 
        'lesson': lesson,
        'comments': comments,
        'comment_form': form,
        'is_completed': is_completed
    })

def news(request):
    # Placeholder
    return render(request, 'core/news.html')

def about(request):
    return render(request, 'core/about.html')

def contact(request):
    return render(request, 'core/contact.html')

@login_required
def members(request):
    # 1. Plan Status
    user_profile = getattr(request.user, 'profile', None)
    current_plan = user_profile.current_plan if user_profile else None

    # 2. Payment History
    payments = PaymentHistory.objects.filter(user=request.user)

    # 3. Replies to comments
    # Find comments where the parent is one of the user's comments
    user_comments = Comment.objects.filter(user=request.user)
    replies = Comment.objects.filter(parent__in=user_comments, active=True).order_by('-created_at')

    # 4. Course Progress
    courses = Course.objects.filter(status='published')
    course_data = []
    
    for course in courses:
        total_lessons = course.lessons.count()
        if total_lessons > 0:
            completed_lessons = CourseProgress.objects.filter(user=request.user, lesson__course=course).count()
            progress_percent = int((completed_lessons / total_lessons) * 100)
        else:
            progress_percent = 0
            
        course_data.append({
            'course': course,
            'progress': progress_percent
        })

    return render(request, 'core/members.html', {
        'current_plan': current_plan,
        'payments': payments,
        'replies': replies,
        'course_data': course_data
    })

@login_required
def mark_lesson_completed(request, lesson_id):
    if request.method == 'POST':
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        # Check if it's an AJAX request
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            progress, created = CourseProgress.objects.get_or_create(user=request.user, lesson=lesson)
            if not created:
                # If already exists, toggle it off (delete)
                progress.delete()
                return JsonResponse({'status': 'unmarked', 'message': 'Aula marcada como não concluída.'})
            return JsonResponse({'status': 'marked', 'message': 'Aula marcada como concluída!'})

        CourseProgress.objects.get_or_create(user=request.user, lesson=lesson)
        messages.success(request, 'Aula marcada como concluída!')
        return redirect('lesson_detail', course_slug=lesson.course.slug, lesson_id=lesson.id)
    return redirect('home')

def subscribe(request):
    apoiador = Plan.objects.filter(name='Apoiador').first()
    irrestrito = Plan.objects.filter(name='Irrestrito').first()
    mecenas = Plan.objects.filter(name='Mecenas').first()
    
    context = {
        'apoiador': apoiador,
        'irrestrito': irrestrito,
        'mecenas': mecenas,
    }
    return render(request, 'core/subscribe.html', context)

def serve_protected_pdf(request, slug):
    article = get_object_or_404(Article, slug=slug, status='published')
    
    if not check_plan_access(request.user, article.required_plan):
        return HttpResponseForbidden("Você não tem permissão para acessar este documento.")

    if not article.pdf_file:
        raise Http404("PDF not found")
    
    # Open the file using the storage backend (which handles decryption)
    try:
        file_handle = article.pdf_file.open()
        response = FileResponse(file_handle, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="{}.pdf"'.format(article.slug)
        # Add headers to prevent caching and discourage saving
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        return response
    except Exception:
        raise Http404("Error reading PDF")

def shop(request):
    items = ShopItem.objects.filter(active=True)
    return render(request, 'core/shop.html', {'items': items})
