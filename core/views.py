from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.contrib import messages
from .models import Article, Course, Lesson, Plan

def check_plan_access(user, required_plan):
    if not required_plan:
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
    articles = Article.objects.filter(status='published')
    
    if category:
        articles = articles.filter(category=category)
        
    courses = Course.objects.filter(status='published')
    return render(request, 'core/content_list.html', {
        'articles': articles, 
        'courses': courses,
        'current_category': category
    })

def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, status='published')
    
    if not check_plan_access(request.user, article.required_plan):
        if not request.user.is_authenticated:
            return redirect('login') # Or whatever your login url name is
        messages.warning(request, 'Este conteúdo requer um plano superior.')
        return redirect('subscribe')
        
    return render(request, 'core/article_detail.html', {'article': article})

def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug, status='published')
    return render(request, 'core/course_detail.html', {'course': course})

def lesson_detail(request, course_slug, lesson_id):
    course = get_object_or_404(Course, slug=course_slug, status='published')
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    return render(request, 'core/lesson_detail.html', {'course': course, 'lesson': lesson})

def news(request):
    # Placeholder
    return render(request, 'core/news.html')

def about(request):
    return render(request, 'core/about.html')

def contact(request):
    return render(request, 'core/contact.html')

@login_required
def members(request):
    return render(request, 'core/members.html')

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
    return render(request, 'core/subscribe.html')
