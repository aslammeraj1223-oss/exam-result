# ================================================================================
# views.py - Django Views for Quiz/Exam Application
# Author: Student
# Description: Contains views for course management, lesson display, exam handling,
#              and result display including submit and show_exam_result functions
# ================================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import json

from .models import (
    Course, Lesson, Question, Choice, Submission, Quiz, QuizResult
)

# ================================================================================
# COURSE VIEWS
# ================================================================================

def course_list(request):
    """
    Display a list of all available courses with search and filtering.
    
    Context:
    - courses: Paginated list of courses
    - search_query: Search term from query parameter
    - filter_level: Difficulty level filter
    """
    courses = Course.objects.filter(is_active=True).annotate(
        lesson_count=Count('lessons'),
        student_count=Count('students'),
        avg_rating=Avg('ratings__rating')
    )
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        courses = courses.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(instructor__username__icontains=search_query)
        )
    
    # Filter by level
    level_filter = request.GET.get('level', '')
    if level_filter:
        courses = courses.filter(level=level_filter)
    
    # Pagination
    paginator = Paginator(courses.order_by('-created_at'), 12)
    page_number = request.GET.get('page')
    courses_page = paginator.get_page(page_number)
    
    context = {
        'courses': courses_page,
        'search_query': search_query,
        'filter_level': level_filter,
    }
    return render(request, 'course_list.html', context)


def course_detail(request, course_id):
    """
    Display detailed information about a specific course and its lessons.
    
    Context:
    - course: Course object with related lessons
    - is_enrolled: Boolean indicating if user is enrolled
    - lessons: All lessons in the course
    """
    course = get_object_or_404(Course, id=course_id, is_active=True)
    
    # Check if user is enrolled
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = course.students.filter(id=request.user.id).exists()
    
    # Get lessons with question count
    lessons = course.lessons.annotate(
        question_count=Count('questions')
    ).order_by('order')
    
    context = {
        'course': course,
        'lessons': lessons,
        'is_enrolled': is_enrolled,
    }
    return render(request, 'course_details_bootstrap.html', context)


@login_required(login_url='login')
def enroll_course(request, course_id):
    """
    Enroll a user in a course.
    
    Args:
    - course_id: ID of the course to enroll in
    
    Redirects to course detail page with success message
    """
    course = get_object_or_404(Course, id=course_id)
    
    if course.students.filter(id=request.user.id).exists():
        messages.warning(request, 'You are already enrolled in this course.')
    else:
        course.students.add(request.user)
        messages.success(request, f'Successfully enrolled in {course.name}!')
    
    return redirect('course-detail', course_id=course_id)


# ================================================================================
# LESSON VIEWS
# ================================================================================

@login_required(login_url='login')
def lesson_detail(request, lesson_id):
    """
    Display a specific lesson with its content and related quiz.
    
    Context:
    - lesson: Lesson object
    - course: Related course
    - is_completed: Boolean indicating if user completed the lesson
    - quiz: Related quiz if available
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course_set.first()
    
    # Check if user is enrolled in the course
    if course and not course.students.filter(id=request.user.id).exists():
        return HttpResponseForbidden('You are not enrolled in this course.')
    
    # Check if lesson is completed
    is_completed = lesson.completed_by.filter(id=request.user.id).exists()
    
    # Get related quiz
    quiz = lesson.quizzes.first() if hasattr(lesson, 'quizzes') else None
    
    context = {
        'lesson': lesson,
        'course': course,
        'is_completed': is_completed,
        'quiz': quiz,
    }
    return render(request, 'lesson_detail.html', context)


@login_required(login_url='login')
def mark_lesson_complete(request, lesson_id):
    """
    Mark a lesson as completed by the user.
    
    Args:
    - lesson_id: ID of the lesson to mark as complete
    
    Returns: JSON response with success status
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    if request.method == 'POST':
        lesson.completed_by.add(request.user)
        return JsonResponse({
            'status': 'success',
            'message': 'Lesson marked as complete!'
        })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=400)


# ================================================================================
# QUIZ/EXAM VIEWS
# ================================================================================

@login_required(login_url='login')
def quiz_start(request, quiz_id):
    """
    Display the starting page of a quiz with instructions and options.
    
    Context:
    - quiz: Quiz object
    - question_count: Number of questions in the quiz
    - duration: Duration of the quiz in minutes
    """
    quiz = get_object_or_404(Quiz, id=quiz_id)
    question_count = quiz.questions.count()
    
    context = {
        'quiz': quiz,
        'question_count': question_count,
    }
    return render(request, 'quiz_start.html', context)


@login_required(login_url='login')
def quiz_questions(request, quiz_id):
    """
    Display quiz questions for the user to answer.
    
    Context:
    - quiz: Quiz object
    - questions: All questions in the quiz
    - total_questions: Total number of questions
    """
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()
    
    if request.method == 'POST':
        # Handle quiz submission
        return submit_exam(request, quiz_id)
    
    context = {
        'quiz': quiz,
        'questions': questions,
        'total_questions': questions.count(),
    }
    return render(request, 'quiz_questions.html', context)


# ================================================================================
# SUBMIT AND SHOW EXAM RESULT FUNCTIONS - MAIN FUNCTIONS
# ================================================================================

@login_required(login_url='login')
@require_http_methods(['POST'])
def submit(request, quiz_id):
    """
    Main function to handle quiz/exam submission.
    
    This function processes the user's answers, calculates the score,
    and creates a quiz result record.
    
    Args:
    - request: HTTP request object containing form data
    - quiz_id: ID of the quiz being submitted
    
    Returns:
    - Redirect to show_exam_result page with quiz_result_id
    
    Features:
    - Validates quiz existence
    - Processes all submitted answers
    - Calculates scores automatically
    - Saves submission records
    - Handles multiple choice and text answers
    - Updates user progress
    - Includes error handling
    
    Process Flow:
    1. Retrieve and validate quiz
    2. Get all questions from the quiz
    3. Iterate through submitted answers
    4. Check correctness for each answer
    5. Calculate total score
    6. Create Submission records for each question
    7. Create QuizResult record
    8. Redirect to results page
    """
    
    try:
        # Step 1: Get and validate the quiz
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # Check if quiz is active
        if not quiz.is_active:
            messages.error(request, 'This quiz is not available.')
            return redirect('course-list')
        
        # Get quiz start time to track duration
        quiz_start_time = request.POST.get('quiz_start_time')
        
        # Step 2: Get all questions in the quiz
        questions = quiz.questions.all()
        
        if not questions.exists():
            messages.error(request, 'This quiz has no questions.')
            return redirect('course-list')
        
        # Step 3: Initialize scoring variables
        total_questions = questions.count()
        correct_answers = 0
        submissions_list = []
        quiz_start_dt = datetime.fromisoformat(quiz_start_time) if quiz_start_time else timezone.now()
        
        # Step 4: Process each question's answer
        for question in questions:
            # Get the user's answer from the POST request
            answer_key = f'question_{question.id}'
            user_answer = request.POST.get(answer_key)
            
            is_correct = False
            selected_choice = None
            answer_text = None
            score = 0
            
            # Handle different question types
            if question.question_type == 'multiple_choice':
                # For multiple choice questions
                if user_answer:
                    selected_choice = get_object_or_404(Choice, id=user_answer, question=question)
                    is_correct = selected_choice.is_correct
                    if is_correct:
                        correct_answers += 1
                        score = 100  # Full marks for correct answer
                    else:
                        score = 0
            
            elif question.question_type == 'short_answer':
                # For short answer questions (basic text matching)
                if user_answer:
                    answer_text = user_answer.strip()
                    correct_choice = question.get_correct_choice()
                    if correct_choice:
                        is_correct = answer_text.lower() == correct_choice.choice_text.lower()
                        if is_correct:
                            correct_answers += 1
                            score = 100
            
            elif question.question_type == 'true_false':
                # For true/false questions
                if user_answer:
                    selected_choice = get_object_or_404(Choice, id=user_answer, question=question)
                    is_correct = selected_choice.is_correct
                    if is_correct:
                        correct_answers += 1
                        score = 100
            
            elif question.question_type == 'essay':
                # For essay questions (no auto-grading, manual review)
                if user_answer:
                    answer_text = user_answer.strip()
                    score = 0  # Will be graded manually
                    is_correct = False  # Mark as pending review
            
            # Step 5: Create Submission record for this question
            submission = Submission(
                user=request.user,
                question=question,
                selected_choice=selected_choice,
                answer_text=answer_text,
                is_correct=is_correct,
                score=score,
                time_taken=0  # Can be calculated if needed
            )
            submissions_list.append(submission)
        
        # Step 6: Bulk create all submissions
        Submission.objects.bulk_create(submissions_list)
        
        # Step 7: Calculate final score as percentage
        final_score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        final_score = round(final_score, 2)
        
        # Step 8: Determine if user passed
        passed = final_score >= quiz.passing_score
        
        # Step 9: Create QuizResult record
        quiz_result = QuizResult.objects.create(
            user=request.user,
            quiz=quiz,
            score=final_score,
            passed=passed,
            started_at=quiz_start_dt,
            completed_at=timezone.now(),
            total_questions=total_questions,
            correct_answers=correct_answers
        )
        
        # Step 10: Send success message
        messages.success(
            request,
            f'Quiz submitted successfully! Your score: {final_score:.1f}%'
        )
        
        # Step 11: Redirect to results page
        return redirect('show-exam-result', quiz_result_id=quiz_result.id)
    
    except Exception as e:
        # Error handling
        messages.error(request, f'An error occurred while submitting the quiz: {str(e)}')
        return redirect('course-list')


@login_required(login_url='login')
def show_exam_result(request, quiz_result_id):
    """
    Display detailed exam/quiz results to the user.
    
    This function shows comprehensive information about the user's quiz
    performance including score, correct/incorrect answers, and detailed
    feedback for each question.
    
    Args:
    - request: HTTP request object
    - quiz_result_id: ID of the QuizResult to display
    
    Returns:
    - Rendered template with result details
    
    Features:
    - Displays overall score and pass/fail status
    - Shows correct vs. incorrect answers
    - Provides detailed feedback for each question
    - Shows time taken for the quiz
    - Displays correct answers for review
    - Includes option to retake quiz
    - Shows score compared to passing score
    - Calculates and displays accuracy percentage
    
    Context Variables:
    - quiz_result: The QuizResult object
    - quiz: Related quiz object
    - questions_with_answers: Questions with user's answers and correct answers
    - score_percentage: User's score as percentage
    - is_passed: Boolean indicating if user passed
    - passing_score: Required score to pass
    - correct_count: Number of correct answers
    - incorrect_count: Number of incorrect answers
    - accuracy_percentage: Accuracy of user's answers
    """
    
    try:
        # Step 1: Get and validate the quiz result
        quiz_result = get_object_or_404(QuizResult, id=quiz_result_id)
        
        # Step 2: Security check - ensure user viewing their own results
        if quiz_result.user != request.user and not request.user.is_staff:
            return HttpResponseForbidden('You do not have permission to view these results.')
        
        # Step 3: Get the related quiz
        quiz = quiz_result.quiz
        
        # Step 4: Retrieve all submissions for this quiz result
        submissions = Submission.objects.filter(
            user=request.user,
            question__in=quiz.questions.all()
        ).select_related('question', 'selected_choice')
        
        # Step 5: Build detailed results with questions and answers
        questions_with_answers = []
        
        for submission in submissions:
            question = submission.question
            correct_choice = question.get_correct_choice()
            
            # Determine user's answer display text
            user_answer_text = ''
            if submission.selected_choice:
                user_answer_text = submission.selected_choice.choice_text
            elif submission.answer_text:
                user_answer_text = submission.answer_text
            else:
                user_answer_text = 'No answer provided'
            
            # Build question detail dictionary
            question_detail = {
                'question': question,
                'user_answer': user_answer_text,
                'correct_answer': correct_choice.choice_text if correct_choice else 'N/A',
                'is_correct': submission.is_correct,
                'score': submission.score,
                'user_submission': submission,
                'question_type': question.get_question_type_display(),
                'choices': question.choice_set.all() if question.question_type == 'multiple_choice' else None,
            }
            questions_with_answers.append(question_detail)
        
        # Step 6: Calculate statistics
        score_percentage = quiz_result.score
        correct_count = quiz_result.correct_answers
        total_count = quiz_result.total_questions
        incorrect_count = total_count - correct_count
        
        # Calculate accuracy
        accuracy_percentage = (correct_count / total_count * 100) if total_count > 0 else 0
        accuracy_percentage = round(accuracy_percentage, 2)
        
        # Step 7: Determine performance level
        if score_percentage >= 90:
            performance_level = 'Excellent'
            performance_color = 'success'
        elif score_percentage >= 80:
            performance_level = 'Very Good'
            performance_color = 'info'
        elif score_percentage >= 70:
            performance_level = 'Good'
            performance_color = 'primary'
        elif score_percentage >= quiz.passing_score:
            performance_level = 'Passed'
            performance_color = 'warning'
        else:
            performance_level = 'Failed'
            performance_color = 'danger'
        
        # Step 8: Check if user can retake the quiz
        can_retake = True
        if hasattr(quiz, 'max_attempts') and quiz.max_attempts:
            user_attempts = QuizResult.objects.filter(
                user=request.user,
                quiz=quiz
            ).count()
            can_retake = user_attempts < quiz.max_attempts
        
        # Step 9: Prepare context data
        context = {
            'quiz_result': quiz_result,
            'quiz': quiz,
            'questions_with_answers': questions_with_answers,
            'score_percentage': score_percentage,
            'is_passed': quiz_result.passed,
            'passing_score': quiz.passing_score,
            'correct_count': correct_count,
            'incorrect_count': incorrect_count,
            'total_count': total_count,
            'accuracy_percentage': accuracy_percentage,
            'performance_level': performance_level,
            'performance_color': performance_color,
            'can_retake': can_retake,
            'time_taken': quiz_result.completed_at - quiz_result.started_at,
        }
        
        # Step 10: Render the results template
        return render(request, 'exam_results.html', context)
    
    except QuizResult.DoesNotExist:
        messages.error(request, 'Quiz result not found.')
        return redirect('course-list')
    
    except Exception as e:
        messages.error(request, f'An error occurred while loading results: {str(e)}')
        return redirect('course-list')


# ================================================================================
# ADDITIONAL UTILITY VIEWS
# ================================================================================

@login_required(login_url='login')
def user_quiz_history(request):
    """
    Display user's quiz history with all attempts and scores.
    
    Context:
    - quiz_results: User's quiz results with pagination
    - average_score: Average score across all quizzes
    - quizzes_completed: Total number of quizzes completed
    """
    quiz_results = QuizResult.objects.filter(user=request.user).select_related(
        'quiz'
    ).order_by('-completed_at')
    
    # Pagination
    paginator = Paginator(quiz_results, 10)
    page_number = request.GET.get('page')
    results_page = paginator.get_page(page_number)
    
    # Calculate statistics
    average_score = quiz_results.aggregate(Avg('score'))['score__avg'] or 0
    average_score = round(average_score, 2)
    quizzes_completed = quiz_results.count()
    passed_count = quiz_results.filter(passed=True).count()
    
    context = {
        'quiz_results': results_page,
        'average_score': average_score,
        'quizzes_completed': quizzes_completed,
        'passed_count': passed_count,
    }
    return render(request, 'quiz_history.html', context)


@login_required(login_url='login')
def quiz_review(request, quiz_id):
    """
    Allow user to review a quiz they completed.
    
    Context:
    - quiz: Quiz object
    - user_result: User's best/last attempt
    - questions_with_answers: Detailed question review
    """
    quiz = get_object_or_404(Quiz, id=quiz_id)
    user_result = QuizResult.objects.filter(
        user=request.user,
        quiz=quiz
    ).order_by('-completed_at').first()
    
    if not user_result:
        messages.error(request, 'You have not completed this quiz yet.')
        return redirect('course-list')
    
    # This uses the same result display logic as show_exam_result
    return show_exam_result(request, user_result.id)


@login_required(login_url='login')
def dashboard(request):
    """
    Display user dashboard with progress, statistics, and recommendations.
    
    Context:
    - enrolled_courses: User's enrolled courses
    - quiz_results: Recent quiz results
    - average_score: Average quiz score
    - total_lessons_completed: Total lessons completed
    - courses_in_progress: Courses with incomplete lessons
    """
    enrolled_courses = Course.objects.filter(
        students=request.user
    ).annotate(
        lesson_count=Count('lessons'),
        completed_lessons=Count('lessons', filter=Q(lessons__completed_by=request.user))
    )
    
    recent_results = QuizResult.objects.filter(
        user=request.user
    ).order_by('-completed_at')[:5]
    
    average_score = recent_results.aggregate(Avg('score'))['score__avg'] or 0
    average_score = round(average_score, 2)
    
    context = {
        'enrolled_courses': enrolled_courses,
        'recent_results': recent_results,
        'average_score': average_score,
        'courses_count': enrolled_courses.count(),
    }
    return render(request, 'dashboard.html', context)


# ================================================================================
# END OF VIEWS
# ================================================================================

"""
URL CONFIGURATION EXAMPLES:

urlpatterns = [
    # Course URLs
    path('courses/', course_list, name='course-list'),
    path('course/<int:course_id>/', course_detail, name='course-detail'),
    path('course/<int:course_id>/enroll/', enroll_course, name='enroll-course'),
    
    # Lesson URLs
    path('lesson/<int:lesson_id>/', lesson_detail, name='lesson-detail'),
    path('lesson/<int:lesson_id>/complete/', mark_lesson_complete, name='lesson-complete'),
    
    # Quiz URLs
    path('quiz/<int:quiz_id>/start/', quiz_start, name='quiz-start'),
    path('quiz/<int:quiz_id>/questions/', quiz_questions, name='quiz-questions'),
    path('quiz/<int:quiz_id>/submit/', submit, name='submit-quiz'),
    path('quiz/result/<int:quiz_result_id>/', show_exam_result, name='show-exam-result'),
    path('quiz/<int:quiz_id>/review/', quiz_review, name='quiz-review'),
    path('quiz-history/', user_quiz_history, name='quiz-history'),
    
    # Dashboard
    path('dashboard/', dashboard, name='dashboard'),
]

REQUEST DATA EXAMPLES:

# Quiz submission form data (POST):
{
    'quiz_start_time': '2024-01-15T10:30:00',
    'question_1': '3',  # Choice ID for multiple choice
    'question_2': 'True',  # For true/false
    'question_3': 'User text answer',  # For short answer
    'question_4': 'Long essay text here...',  # For essay
}

RESPONSE/REDIRECT:
- Successful submission: Redirects to show_exam_result with quiz_result_id
- Error: Redirects to course_list with error message

MODEL RELATIONSHIPS:
- QuizResult.user → User
- QuizResult.quiz → Quiz
- Submission.user → User
- Submission.question → Question
- Submission.selected_choice → Choice (nullable)
- Quiz.questions → ManyToMany with Question
- Course.students → ManyToMany with User
"""
