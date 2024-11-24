from django.urls import path
from . import views
from django.contrib import admin



urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('home/', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('create-quiz/', views.create_quiz, name='create_quiz'),
    path('manage-quiz/', views.manage_quiz, name='manage_quiz'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('take-quiz/', views.take_quiz, name='take_quiz'),
    path('attempt-quiz/<int:quiz_id>/', views.attempt_quiz, name='attempt_quiz'),
    path('quiz-results/<int:quiz_id>/<int:score>/<int:total_questions>/<int:percentage>/', views.quiz_results, name='quiz_results'),
    path('edit_quiz/<int:quiz_id>/', views.edit_quiz, name='edit_quiz'),
    path('delete_quiz/<int:quiz_id>/', views.delete_quiz, name='delete_quiz'),
    path('edit_question/<int:quiz_id>/', views.edit_question, name='edit_question'),
    path('delete_question/<int:quiz_id>/', views.delete_question, name='delete_question'),
    path('add_question/<int:quiz_id>/', views.add_question, name='add_question')
]

