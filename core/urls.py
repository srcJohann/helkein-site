from django.urls import path
from . import views
from . import views_payment

urlpatterns = [
    path('', views.home, name='home'),
    path('conteudo/', views.content_list, name='content_list'),
    path('conteudo/<slug:slug>/pdf/', views.serve_protected_pdf, name='serve_protected_pdf'),
    path('conteudo/<slug:slug>/', views.article_detail, name='article_detail'),
    path('cursos/<slug:slug>/', views.course_detail, name='course_detail'),
    path('cursos/<slug:course_slug>/aula/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('novidades/', views.news, name='news'),
    path('sobre/', views.about, name='about'),
    path('contato/', views.contact, name='contact'),
    path('membros/', views.members, name='members'),
    path('associe-se/', views.subscribe, name='subscribe'),
    
    # Payment URLs
    path('pagamento/checkout/<int:plan_id>/', views_payment.create_checkout_session, name='create_checkout_session'),
    path('pagamento/sucesso/', views_payment.payment_success, name='payment_success'),
    path('pagamento/cancelado/', views_payment.payment_cancel, name='payment_cancel'),
    path('webhook/stripe/', views_payment.stripe_webhook, name='stripe_webhook'),
]