from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from .storage import EncryptedFileSystemStorage

class Plan(models.Model):
    name = models.CharField(max_length=50)
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True)
    level = models.IntegerField(default=0, help_text="Higher level means more access")

    class Meta:
        verbose_name = "Plano"
        verbose_name_plural = "Planos"

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    current_plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Perfil de Usuário"
        verbose_name_plural = "Perfis de Usuário"
    
    def __str__(self):
        return f"{self.user.username} - {self.current_plan}"

class Article(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    CATEGORY_CHOICES = [
        ('artigo', 'Artigo'),
        ('ensaio', 'Ensaio'),
        ('resenha', 'Resenha'),
        ('recomendacao', 'Recomendação Bibliográfica'),
        ('multimidia', 'Multimídia'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='artigo')
    summary = models.TextField()
    content = models.TextField(blank=True, default='')
    tags = models.CharField(max_length=200, help_text="Comma separated tags")
    authors = models.ManyToManyField(User, related_name='articles')
    pdf_file = models.FileField(
        upload_to='articles/pdfs/', 
        blank=True, 
        null=True,
        storage=EncryptedFileSystemStorage()
    )
    cover_image = models.ImageField(upload_to='articles/covers/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True, help_text="URL do vídeo para conteúdo multimídia")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    required_plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',')] if self.tags else []

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Artigo(Article):
    class Meta:
        proxy = True
        verbose_name = "Artigo"
        verbose_name_plural = "Artigos"

class Ensaio(Article):
    class Meta:
        proxy = True
        verbose_name = "Ensaio"
        verbose_name_plural = "Ensaios"

class Resenha(Article):
    class Meta:
        proxy = True
        verbose_name = "Resenha"
        verbose_name_plural = "Resenhas"

class Recomendacao(Article):
    class Meta:
        proxy = True
        verbose_name = "Recomendação"
        verbose_name_plural = "Recomendações"

class Multimidia(Article):
    class Meta:
        proxy = True
        verbose_name = "Multimídia"
        verbose_name_plural = "Multimídia"

class Course(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    cover_image = models.ImageField(upload_to='courses/covers/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = "Módulo"
        verbose_name_plural = "Módulos"

    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    module = models.ForeignKey(Module, on_delete=models.SET_NULL, related_name='lessons', null=True, blank=True)
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField()
    vimeo_video_id = models.CharField(max_length=100, blank=True, null=True)
    duration = models.CharField(max_length=10, blank=True, null=True, help_text="Duration in MM:SS")
    materials = models.FileField(upload_to='lessons/materials/', blank=True, null=True)
    required_plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['order']
        verbose_name = "Aula"
        verbose_name_plural = "Aulas"

    def __str__(self):
        return f"{self.course.title} - {self.title}"
