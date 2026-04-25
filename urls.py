# ================================================================================
# urls.py - Django URL Configuration for Quiz/Exam Application
# Author: Student
# Description: Contains URL patterns for course management, lesson display,
#              quiz handling, and result display including submit and
#              show_exam_result URL paths
# ================================================================================

from django.urls import path
from . import views

# App name for URL namespacing
app_name = 'quiz'

urlpatterns = [
    
    # ========================================================================
    # COURSE MANAGEMENT URLs
    # ========================================================================
    
    # Course list view - Display all available courses
    path(
        'courses/',
        views.course_list,
        name='course-list'
    ),
    
    # Course detail view - Display specific course with lessons
    path(
        'course/<int:course_id>/',
        views.course_detail,
        name='course-detail'
    ),
    
    # Enroll in course - Add user to course students
    path(
        'course/<int:course_id>/enroll/',
        views.enroll_course,
        name='enroll-course'
    ),
    
    # ========================================================================
    # LESSON MANAGEMENT URLs
    # ========================================================================
    
    # Lesson detail view - Display lesson content
    path(
        'lesson/<int:lesson_id>/',
        views.lesson_detail,
        name='lesson-detail'
    ),
    
    # Mark lesson as complete - Update lesson completion status
    path(
        'lesson/<int:lesson_id>/complete/',
        views.mark_lesson_complete,
        name='lesson-complete'
    ),
    
    # ========================================================================
    # QUIZ/EXAM URLs - MAIN SUBMISSION AND RESULTS PATHS
    # ========================================================================
    
    # Quiz start view - Show quiz instructions and options
    path(
        'quiz/<int:quiz_id>/start/',
        views.quiz_start,
        name='quiz-start'
    ),
    
    # Quiz questions view - Display all quiz questions
    path(
        'quiz/<int:quiz_id>/questions/',
        views.quiz_questions,
        name='quiz-questions'
    ),
    
    # ========================================================================
    # CRITICAL: QUIZ SUBMISSION URL PATH
    # ========================================================================
    # URL: /quiz/<quiz_id>/submit/
    # Method: POST
    # Function: submit()
    # Purpose: Handle quiz/exam submission
    # Features:
    # - Process all submitted answers
    # - Calculate scores automatically
    # - Validate answers and questions
    # - Create submission records
    # - Generate quiz results
    # - Redirect to show_exam_result page
    # ========================================================================
    
    path(
        'quiz/<int:quiz_id>/submit/',
        views.submit,
        name='submit-quiz'
    ),
    
    # ========================================================================
    # CRITICAL: EXAM RESULT DISPLAY URL PATH
    # ========================================================================
    # URL: /quiz/result/<quiz_result_id>/
    # Method: GET
    # Function: show_exam_result()
    # Purpose: Display detailed exam results
    # Features:
    # - Show final score and percentage
    # - Display correct/incorrect answers
    # - Provide question-by-question feedback
    # - Calculate accuracy and performance level
    # - Allow quiz review and retake
    # - Include performance statistics
    # ========================================================================
    
    path(
        'quiz/result/<int:quiz_result_id>/',
        views.show_exam_result,
        name='show-exam-result'
    ),
    
    # Quiz review view - Review a previously completed quiz
    path(
        'quiz/<int:quiz_id>/review/',
        views.quiz_review,
        name='quiz-review'
    ),
    
    # ========================================================================
    # QUIZ HISTORY AND ANALYTICS URLs
    # ========================================================================
    
    # User quiz history - Show all quiz attempts and results
    path(
        'quiz-history/',
        views.user_quiz_history,
        name='quiz-history'
    ),
    
    # ========================================================================
    # USER DASHBOARD Urls
    # ========================================================================
    
    # User dashboard - Main dashboard with progress and stats
    path(
        'dashboard/',
        views.dashboard,
        name='dashboard'
    ),
    
]

# ================================================================================
# URL PATTERN DOCUMENTATION
# ================================================================================

"""
COMPLETE URL CONFIGURATION REFERENCE:

1. COURSE URLS:
   - /courses/ ............................ List all courses
   - /course/1/ ........................... View course details
   - /course/1/enroll/ .................... Enroll in a course

2. LESSON URLS:
   - /lesson/5/ ........................... View lesson content
   - /lesson/5/complete/ .................. Mark lesson as completed

3. QUIZ URLS:
   *** SUBMIT QUIZ (POST REQUEST) ***
   - /quiz/3/submit/ ...................... Submit quiz answers (PRIMARY ENDPOINT)
     * Method: POST
     * Data: Form data with question answers
     * Redirect: show-exam-result

   *** SHOW EXAM RESULT (GET REQUEST) ***
   - /quiz/result/15/ ..................... Display exam results (PRIMARY ENDPOINT)
     * Method: GET
     * Variables: quiz_result_id = 15
     * Display: Detailed score, feedback, correct answers

   OTHER QUIZ URLS:
   - /quiz/3/start/ ....................... Start quiz with instructions
   - /quiz/3/questions/ ................... Display quiz questions
   - /quiz/3/review/ ...................... Review previous quiz attempt

4. USER URLS:
   - /quiz-history/ ....................... View all quiz attempts
   - /dashboard/ .......................... User dashboard and progress


USAGE EXAMPLES IN TEMPLATES:

1. LINKING TO SUBMIT QUIZ:
   <form method="post" action="{% url 'quiz:submit-quiz' quiz.id %}">
       {% csrf_token %}
       <input type="hidden" name="quiz_start_time" value="{{ start_time }}">
       
       {% for question in quiz.questions.all %}
           <div class="question">
               <label>{{ question.question_text }}</label>
               {% if question.question_type == 'multiple_choice' %}
                   {% for choice in question.choice_set.all %}
                       <input type="radio" 
                              name="question_{{ question.id }}" 
                              value="{{ choice.id }}">
                       {{ choice.choice_text }}
                   {% endfor %}
               {% endif %}
           </div>
       {% endfor %}
       
       <button type="submit">Submit Quiz</button>
   </form>

2. LINKING TO EXAM RESULTS:
   <a href="{% url 'quiz:show-exam-result' quiz_result.id %}">
       View Results
   </a>

3. LINKING TO QUIZ START:
   <a href="{% url 'quiz:quiz-start' quiz.id %}" class="btn btn-primary">
       Start Quiz
   </a>

4. LINKING TO COURSE:
   <a href="{% url 'quiz:course-detail' course.id %}">
       {{ course.name }}
   </a>

5. LINKING TO LESSON:
   <a href="{% url 'quiz:lesson-detail' lesson.id %}">
       {{ lesson.title }}
   </a>

6. LINKING TO QUIZ HISTORY:
   <a href="{% url 'quiz:quiz-history' %}">
       My Quiz History
   </a>

7. LINKING TO DASHBOARD:
   <a href="{% url 'quiz:dashboard' %}">
       My Dashboard
   </a>


DJANGO REVERSE URL LOOKUP:

In views.py, use reverse() to generate URLs:

   from django.urls import reverse
   
   # Generate submit URL
   submit_url = reverse('quiz:submit-quiz', args=[quiz_id])
   
   # Generate result URL
   result_url = reverse('quiz:show-exam-result', args=[quiz_result_id])
   
   # Generate course URL
   course_url = reverse('quiz:course-detail', args=[course_id])


FORM ACTION EXAMPLES:

1. Quiz submission form:
   <form method="post" action="{% url 'quiz:submit-quiz' quiz.id %}">
       {% csrf_token %}
       <!-- form fields -->
   </form>

2. Lesson completion:
   <form method="post" action="{% url 'quiz:lesson-complete' lesson.id %}">
       {% csrf_token %}
       <button type="submit">Mark as Complete</button>
   </form>

3. Course enrollment:
   <form method="post" action="{% url 'quiz:enroll-course' course.id %}">
       {% csrf_token %}
       <button type="submit">Enroll Now</button>
   </form>


URL PARAMETERS:

- quiz_id: Primary key of Quiz model
  Example: /quiz/5/submit/

- quiz_result_id: Primary key of QuizResult model
  Example: /quiz/result/42/

- course_id: Primary key of Course model
  Example: /course/3/

- lesson_id: Primary key of Lesson model
  Example: /lesson/7/


NAMESPACING:

app_name = 'quiz'

This allows referencing URLs as:
- {% url 'quiz:submit-quiz' %}
- {% url 'quiz:show-exam-result' %}

Instead of just:
- {% url 'submit-quiz' %}
- {% url 'show-exam-result' %}


PROJECT-LEVEL URLS CONFIGURATION:

In your main project urls.py, include these patterns:

   from django.contrib import admin
   from django.urls import path, include
   
   urlpatterns = [
       path('admin/', admin.site.urls),
       path('', include('your_app.urls')),  # Include app URLs
       # or
       path('quiz/', include('your_app.urls')),  # Prefix with quiz/
   ]

This will make your URLs available as:
- /courses/ or /quiz/courses/
- /quiz/1/submit/ or /quiz/quiz/1/submit/
- /quiz/result/1/ or /quiz/quiz/result/1/


REQUEST FLOW - SUBMIT AND RESULT:

1. USER SUBMITS QUIZ:
   POST /quiz/3/submit/
   └─ views.submit(request, quiz_id=3)
   └─ Process answers
   └─ Calculate score
   └─ Create QuizResult
   └─ Redirect to step 2

2. VIEW RESULTS:
   GET /quiz/result/42/
   └─ views.show_exam_result(request, quiz_result_id=42)
   └─ Fetch result details
   └─ Display score and feedback
   └─ Render exam_results.html


SECURITY NOTES:

- CSRF token required for POST requests ({% csrf_token %})
- @login_required decorator on views restricts access
- URL parameters are validated with get_object_or_404()
- User permissions checked before accessing results
- Integer primary keys used (no string IDs)


QUERY STRING EXAMPLES:

URL patterns can also accept query strings (GET parameters):

- /courses/?search=python&level=beginner
- /quiz-history/?page=2
- /dashboard/?filter=recent


URL NAMING CONVENTIONS USED:

- course-list ........................ Plural for listing
- course-detail ...................... Singular + 'detail'
- enroll-course ...................... Action + object
- lesson-detail ...................... Singular + 'detail'
- lesson-complete .................... Action + object
- quiz-start ......................... Action + object
- quiz-questions ..................... Object + 'questions'
- submit-quiz ........................ Action + object (PRIMARY)
- show-exam-result ................... Action + object (PRIMARY)
- quiz-review ........................ Object + 'review'
- quiz-history ....................... Object + 'history'
- dashboard .......................... Standalone


BEST PRACTICES IMPLEMENTED:

✓ Consistent naming convention
✓ Descriptive URL names
✓ Grouped by functionality
✓ App namespacing for clarity
✓ RESTful-style paths (nouns first)
✓ Proper HTTP methods (GET/POST)
✓ Path parameters for IDs
✓ Clear purpose comments
✓ Comprehensive documentation


COMMON URL PATTERNS:

Detail view: path('item/<int:item_id>/', views.item_detail, name='item-detail')
Action view: path('item/<int:item_id>/action/', views.action, name='action')
List view:   path('items/', views.item_list, name='item-list')
Create view: path('items/new/', views.item_create, name='item-create')


REDIRECTS IMPLEMENTED IN VIEWS:

After successful submit:
   redirect('quiz:show-exam-result', quiz_result_id=quiz_result.id)

After enrollment:
   redirect('quiz:course-detail', course_id=course_id)

After error:
   redirect('quiz:course-list')
"""

# ================================================================================
# END OF URL CONFIGURATION
# ================================================================================
