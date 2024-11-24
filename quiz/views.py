from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, LoginForm, QuizForm, QuestionForm
from .models import Quiz, Question, Answer, QuizResult, Category, QuizAnswer
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.db import transaction

def welcome(request):
    return render(request, 'quiz/welcome.html')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User registered successfully! Please Login to continue.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'quiz/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'User logged in successfully!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password')
                return render(request, 'quiz/login.html', {'form': form, 'error': 'Invalid credentials'})
    else:
        form = LoginForm()
    return render(request, 'quiz/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)

    messages.success(request, 'User logged out successfully!')
    return redirect('login')


@login_required
def create_quiz(request):
    QuestionFormSet = modelformset_factory(
        Question,
        fields=('text', 'question_type'),
        extra=1,
        can_delete=False
    )

    if request.method == 'POST':
        quiz_form = QuizForm(request.POST)
        question_formset = QuestionFormSet(request.POST, prefix='questions')

        new_category_name = request.POST.get('new_category')
        if new_category_name:
            category, created = Category.objects.get_or_create(name=new_category_name)
            quiz_form.instance.category = category

        if quiz_form.is_valid() and question_formset.is_valid():
            with transaction.atomic():
                # Save the quiz
                quiz = quiz_form.save(commit=False)
                quiz.created_by = request.user
                quiz.save()

                # Save questions and answers
                for index, question_form in enumerate(question_formset):
                    question = question_form.save(commit=False)
                    question.quiz = quiz
                    question.save()

                    # Retrieve options and correct answer
                    question_prefix = f'questions-{index}'
                    if question.question_type == 'multiple_choice':
                        options = [
                            request.POST.get(f'{question_prefix}-option_1'),
                            request.POST.get(f'{question_prefix}-option_2'),
                            request.POST.get(f'{question_prefix}-option_3'),
                            request.POST.get(f'{question_prefix}-option_4'),
                        ]
                        correct_option = request.POST.get(f'{question_prefix}-correct_option')

                        # Save options
                        for idx, option_text in enumerate(options, start=1):
                            if option_text:  # Ensure option is not empty
                                Answer.objects.create(
                                    question=question,
                                    text=option_text,
                                    is_correct=(str(idx) == correct_option)
                                )

                    elif question.question_type == 'true_false':
                        correct_option = request.POST.get(f'{question_prefix}-correct_option')
                        Answer.objects.create(
                            question=question,
                            text='True',
                            is_correct=(correct_option == 'True')
                        )
                        Answer.objects.create(
                            question=question,
                            text='False',
                            is_correct=(correct_option == 'False')
                        )
            messages.success(request, 'Quiz created successfully!')  # Add success message
            return redirect('create_quiz')
            
    else:
        quiz_form = QuizForm()
        question_formset = QuestionFormSet(queryset=Question.objects.none(), prefix='questions')

    return render(request, 'quiz/create_quiz.html', {
        'quiz_form': quiz_form,
        'question_formset': question_formset,
    })

@login_required
def manage_quiz(request):
    quizzes = Quiz.objects.filter(created_by=request.user)
    return render(request, 'quiz/manage_quiz.html', {'quizzes': quizzes})

@login_required
def leaderboard(request):
    selected_quiz = request.GET.get('quiz')

    # Filter quizzes based on selected quiz
    quizzes = Quiz.objects.all()
    
    leaderboard_data = []
    if selected_quiz:
        quiz = get_object_or_404(Quiz, id=selected_quiz)
        top_scores = QuizResult.objects.filter(quiz=quiz).order_by('-percentage')[:10]  # Top 10 scorers
        leaderboard_data.append({
            'quiz': quiz,
            'top_scores': top_scores,
        })

    return render(request, 'quiz/leaderboard.html', {
        'leaderboard_data': leaderboard_data,
        'quizzes': quizzes,
        'selected_quiz': selected_quiz,
    })


@login_required
def home(request):
    return render(request, 'quiz/home.html')

@login_required
def take_quiz(request):
    category_filter = request.GET.get('category')  # Get selected category from query params
    if category_filter:
        quizzes = Quiz.objects.filter(category__id=category_filter)  # Filter quizzes by category
    else:
        quizzes = Quiz.objects.all()  # Show all quizzes if no category is selected

    categories = Category.objects.all()  # Fetch all categories for the filter
    context = {
        'quizzes': quizzes,
        'categories': categories,
        'selected_category': int(category_filter) if category_filter else None,
    }
    return render(request, 'quiz/take_quiz.html', context)

@login_required
def attempt_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()

    if request.method == 'POST':
        # Optionally, delete previous answers if retaking the quiz
        QuizAnswer.objects.filter(user=request.user, quiz=quiz).delete()

        score = 0
        total_questions = len(questions)

        for question in questions:
            selected_answer_id = request.POST.get(f"question_{question.id}")
            correct_answer = question.answers.filter(is_correct=True).first()

            if selected_answer_id:
                try:
                    selected_answer = Answer.objects.get(id=selected_answer_id)
                    is_correct = selected_answer == correct_answer
                    if is_correct:
                        score += 1

                    QuizAnswer.objects.create(
                        user=request.user,
                        quiz=quiz,
                        question=question,
                        selected_answer=selected_answer,
                    )
                except Answer.DoesNotExist:
                    # Handle invalid answer selection if necessary
                    pass

        percentage_score = int((score / total_questions) * 100)

        messages.success(request, 'Quiz submitted successfully!')
        return redirect('quiz_results', quiz_id=quiz.id, score=score, total_questions=total_questions, percentage=percentage_score)

    return render(request, 'quiz/attempt_quiz.html', {'quiz': quiz, 'questions': questions})


@login_required
def quiz_results(request, quiz_id, score, total_questions, percentage):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()

    # Prepare a list to hold data for each question
    question_data = []

    for question in questions:
        # Retrieve the user's selected answer for this question
        try:
            quiz_answer = QuizAnswer.objects.get(user=request.user, quiz=quiz, question=question)
            user_selected_answer = quiz_answer.selected_answer
            is_correct = user_selected_answer.is_correct
        except QuizAnswer.DoesNotExist:
            user_selected_answer = None
            is_correct = False

        # Retrieve the correct answer
        correct_answer = question.answers.filter(is_correct=True).first()

        question_data.append({
            'question': question,
            'user_answer': user_selected_answer,
            'is_correct': is_correct,
            'correct_answer': correct_answer,
        })

    # Save the result to the QuizResult model
    QuizResult.objects.create(
        user=request.user,
        quiz=quiz,
        score=score,
        total_questions=total_questions,
        percentage=percentage,
    )

    return render(request, 'quiz/results.html', {
        'quiz': quiz,
        'score': score,
        'total_questions': total_questions,
        'percentage': percentage,
        'question_data': question_data,
    })

@login_required
def edit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    categories = Category.objects.all()

    QuestionFormSet = modelformset_factory(Question, form=QuestionForm, extra=0, can_delete=True)
    question_formset = QuestionFormSet(request.POST or None, queryset=quiz.questions.all())

    if request.method == 'POST':
        # Update quiz details
        quiz.name = request.POST.get('name')
        quiz.description = request.POST.get('description')

        new_category = request.POST.get('new_category')
        if new_category:
            category, _ = Category.objects.get_or_create(name=new_category)
            quiz.category = category
        else:
            quiz.category_id = request.POST.get('category')
        quiz.save()

        # Save questions
        if question_formset.is_valid():
            questions = question_formset.save(commit=False)
            for question in questions:
                question.quiz = quiz
                question.save()

        messages.success(request, 'Quiz details updated successfully!')
        return redirect('edit_quiz')  # Redirect to manage quizzes after saving

    return render(request, 'quiz/edit_quiz.html', {
        'quiz': quiz,
        'categories': categories,
        'question_formset': question_formset,
    })

@login_required
def delete_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=request.user)
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, 'Quiz deleted successfully!')
        return redirect('manage_quiz')
    return redirect('manage_quiz')

@login_required
def edit_question(request, quiz_id):
    # Retrieve the quiz object using the provided quiz_id
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # Retrieve all questions related to the quiz
    questions = quiz.questions.all()  # Assuming 'questions' is the related name for Question model

    # If a specific question_id is provided in the request (for editing)
    question_id = request.GET.get('question_id')
    question = get_object_or_404(Question, id=question_id) if question_id else None
    options = question.answers.all() if question else []

    if request.method == 'POST':
        # Update the question's text and type
        question.text = request.POST.get('text')
        question.save()

        # Update options
        for option in options:
            option_text = request.POST.get(f'option_{option.id}')
            is_correct = request.POST.get(f'is_correct_{option.id}') == 'on'
            option.text = option_text
            option.is_correct = is_correct
            option.save()

        # Redirect back to the edit quiz page after saving
        messages.success(request, 'Question updated successfully!')
        return redirect('edit_question', quiz_id=quiz.id)  # Ensure quiz.id is accessible

    # Render the edit question template with the quiz and its questions
    return render(request, 'quiz/edit_question.html', {
        'quiz': quiz,
        'questions': questions,
        'question': question,
        'options': options,
    })

@login_required
def delete_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        print(quiz_id)
        print(question_id)
        question = get_object_or_404(Question, id=question_id, quiz=quiz)

        print(quiz_id)
        print(question_id)

        question.delete()
        messages.success(request, 'Question deleted successfully!')
        return redirect('delete_question', quiz_id=quiz.id)

    questions = quiz.questions.all()
    return render(request, 'quiz/delete_question.html', {
        'quiz': quiz,
        'questions': questions,
    })

@login_required
def add_question(request, quiz_id):
    # Retrieve the quiz object using the provided quiz_id
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.method == 'POST':
        # Get the question text and type from the form
        question_text = request.POST.get('text')
        question_type = request.POST.get('question_type')
        correct_option = request.POST.get('correct_option')
        print(correct_option)


        # Create the question instance
        question = Question.objects.create(quiz=quiz, text=question_text, question_type=question_type)

        if question_type == 'multiple_choice':
            # Handle multiple-choice options
            for i in range(1, 5):  # Assuming 4 options
                option_text = request.POST.get(f'option_{i}')
                if option_text:  # Only create an answer if the option text is not empty
                    is_correct = correct_option == str(i)
                    Answer.objects.create(question=question, text=option_text, is_correct=is_correct)

        elif question_type == 'true_false':
            # Handle true/false options
            correct_option = request.POST.get('true_false_correct_option')
            # Create answers for True and False
            Answer.objects.create(question=question, text='True', is_correct=(correct_option == 'True'))
            Answer.objects.create(question=question, text='False', is_correct=(correct_option == 'False'))

        # Redirect to the edit quiz page after saving
        messages.success(request, 'Question added successfully!')
        return redirect('add_question', quiz_id=quiz.id)

    return render(request, 'quiz/add_question.html', {'quiz': quiz})