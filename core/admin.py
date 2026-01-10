from django.contrib import admin
from .models import Plan, UserProfile, Article, Course, Lesson, Module, Artigo, Ensaio, Resenha, Recomendacao, Multimidia, Comment, ShopItem, PaymentHistory, DailyVisit

class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'views', 'created_at')
    list_filter = ('status', 'category')
    search_fields = ('title', 'summary', 'content')
    prepopulated_fields = {'slug': ('title',)}

class ContentTypeAdmin(ArticleAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(category=self.category_value)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.category = self.category_value
        super().save_model(request, obj, form, change)

    def get_changeform_initial_data(self, request):
        return {'category': self.category_value}

@admin.register(Artigo)
class ArtigoAdmin(ContentTypeAdmin):
    category_value = 'artigo'

@admin.register(Ensaio)
class EnsaioAdmin(ContentTypeAdmin):
    category_value = 'ensaio'

@admin.register(Resenha)
class ResenhaAdmin(ContentTypeAdmin):
    category_value = 'resenha'

@admin.register(Recomendacao)
class RecomendacaoAdmin(ContentTypeAdmin):
    category_value = 'recomendacao'

@admin.register(Multimidia)
class MultimidiaAdmin(ContentTypeAdmin):
    category_value = 'multimidia'

class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 1
    exclude = ('course',)

class ModuleInline(admin.StackedInline):
    model = Module
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'views', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ModuleInline]

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    inlines = [LessonInline]

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, Lesson):
                if not instance.course_id:
                     instance.course = form.instance.course
            instance.save()
        formset.save_m2m()

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'module', 'order', 'duration')
    list_filter = ('course', 'module')
    search_fields = ('title', 'course__title')

admin.site.register(Plan)
admin.site.register(UserProfile)
admin.site.register(Comment)
admin.site.register(ShopItem)
admin.site.register(PaymentHistory)
admin.site.register(DailyVisit)
# admin.site.register(Article, ArticleAdmin) # Optional: Keep generic view or remove
