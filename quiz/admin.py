from django.contrib import admin
from .models import Quiz, Question, Answer, Category

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'created_by', 'created_at')
    search_fields = ('name', 'category')
    list_filter = ('category',)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'question_type')
    search_fields = ('text', 'quiz__name')
    list_filter = ('question_type', 'quiz')

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    search_fields = ('text', 'question__text')
    list_filter = ('is_correct',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')  # Display these fields in the admin list view
    search_fields = ('name',)  # Add a search bar for the category name
    ordering = ('name',)  # Sort by name