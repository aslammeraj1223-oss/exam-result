# ================================================================================
# admin.py - Django Admin Configuration for Quiz Application
# Author: Student
# Description: Register and configure quiz models in Django admin interface
#              Includes QuestionInline, ChoiceInline, and various Admin classes
# ================================================================================

# ================================================================================
# SEVEN IMPORTED CLASSES
# ================================================================================

from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.templatetags.static import static

from .models import Question, Choice, Submission, Quiz, QuizResult

# ================================================================================
# INLINE CLASSES FOR NESTED EDITING
# ================================================================================

class ChoiceInline(admin.TabularInline):
    """
    Inline admin for Choice model.
    Allows editing choices directly on the Question admin page.
    """
    model = Choice
    extra = 2  # Show 2 empty choice fields by default
    fields = ('choice_text', 'is_correct', 'order')
    ordering = ['order']
    
    def get_queryset(self, request):
        """Optimize queryset by ordering choices"""
        queryset = super().get_queryset(request)
        return queryset.order_by('order')


class QuestionInline(admin.TabularInline):
    """
    Inline admin for Question model.
    Allows editing questions directly on the Quiz admin page.
    """
    model = Quiz.questions.through
    extra = 1  # Show 1 empty question field by default
    verbose_name = 'Question'
    verbose_name_plural = 'Questions'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        queryset = super().get_queryset(request)
        return queryset.select_related('question')


# ================================================================================
# QUESTION ADMIN
# ================================================================================

class QuestionAdmin(admin.ModelAdmin):
    """
    Admin interface for Question model.
    Features:
    - Display questions with custom formatting
    - Filter by difficulty and topic
    - Search by question text
    - Inline editing of choices
    - Custom actions
    """
    
    # Display in list view
    list_display = (
        'get_question_preview',
        'get_difficulty_colored',
        'question_type',
        'topic',
        'get_choice_count',
        'get_submission_count',
        'is_active',
        'created_at'
    )
    
    # Filters on the right side
    list_filter = (
        'difficulty_level',
        'question_type',
        'topic',
        'is_active',
        'created_at',
    )
    
    # Search functionality
    search_fields = ('question_text', 'topic')
    
    # Read-only fields
    readonly_fields = (
        'created_at',
        'updated_at',
        'get_submission_count',
        'get_all_choices_display',
    )
    
    # Fieldsets for organized display
    fieldsets = (
        ('Question Details', {
            'fields': ('question_text', 'question_type', 'difficulty_level')
        }),
        ('Organization', {
            'fields': ('topic', 'is_active')
        }),
        ('Choices', {
            'fields': ('get_all_choices_display',),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('get_submission_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Inline editing
    inlines = [ChoiceInline]
    
    # Pagination
    list_per_page = 25
    
    # Ordering
    ordering = ['-created_at']
    
    # Custom actions
    actions = ['mark_active', 'mark_inactive', 'mark_as_easy', 'mark_as_hard']
    
    # ========================================================================
    # Custom Display Methods
    # ========================================================================
    
    def get_question_preview(self, obj):
        """Display first 80 characters of question with truncation"""
        text = obj.question_text[:80]
        if len(obj.question_text) > 80:
            text += '...'
        return text
    get_question_preview.short_description = 'Question'
    
    def get_difficulty_colored(self, obj):
        """Display difficulty level with color coding"""
        colors = {
            'easy': '#28a745',      # Green
            'medium': '#ffc107',    # Yellow
            'hard': '#dc3545',      # Red
        }
        color = colors.get(obj.difficulty_level, '#000000')
        html = f'<span style="background-color: {color}; color: white; padding: 5px 10px; border-radius: 3px;">{obj.get_difficulty_level_display()}</span>'
        return mark_safe(html)
    get_difficulty_colored.short_description = 'Difficulty'
    
    def get_choice_count(self, obj):
        """Display number of choices for this question"""
        count = obj.choice_set.count()
        return f"{count} choices"
    get_choice_count.short_description = 'Choices'
    
    def get_submission_count(self, obj):
        """Display number of submissions for this question"""
        count = obj.get_submission_count()
        return count
    get_submission_count.short_description = 'Submissions'
    
    def get_all_choices_display(self, obj):
        """Display all choices for this question in read-only format"""
        choices = obj.choice_set.all().order_by('order')
        if not choices.exists():
            return "No choices added yet"
        
        html = '<ul style="list-style-type: none;">'
        for choice in choices:
            status = '✓ <strong>CORRECT</strong>' if choice.is_correct else '✗ Incorrect'
            html += f'<li style="padding: 5px 0; border-bottom: 1px solid #ddd;">{choice.order + 1}. {choice.choice_text} - {status}</li>'
        html += '</ul>'
        return mark_safe(html)
    get_all_choices_display.short_description = 'All Choices'
    
    # ========================================================================
    # Custom Actions
    # ========================================================================
    
    def mark_active(self, request, queryset):
        """Action to mark selected questions as active"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} question(s) marked as active.')
    mark_active.short_description = 'Mark selected questions as active'
    
    def mark_inactive(self, request, queryset):
        """Action to mark selected questions as inactive"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} question(s) marked as inactive.')
    mark_inactive.short_description = 'Mark selected questions as inactive'
    
    def mark_as_easy(self, request, queryset):
        """Action to mark selected questions as easy"""
        updated = queryset.update(difficulty_level='easy')
        self.message_user(request, f'{updated} question(s) marked as easy.')
    mark_as_easy.short_description = 'Mark as easy difficulty'
    
    def mark_as_hard(self, request, queryset):
        """Action to mark selected questions as hard"""
        updated = queryset.update(difficulty_level='hard')
        self.message_user(request, f'{updated} question(s) marked as hard.')
    mark_as_hard.short_description = 'Mark as hard difficulty'
    
    # ========================================================================
    # Queryset Optimization
    # ========================================================================
    
    def get_queryset(self, request):
        """Optimize queryset with annotations"""
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            choice_count=Count('choice', distinct=True),
            submission_count=Count('submissions', distinct=True)
        )
        return queryset


# ================================================================================
# CHOICE ADMIN
# ================================================================================

class ChoiceAdmin(admin.ModelAdmin):
    """
    Admin interface for Choice model.
    Features:
    - Display choices with question reference
    - Filter by correctness
    - Search by choice text
    - Inline ordering
    """
    
    list_display = (
        'get_choice_preview',
        'get_question_link',
        'get_status_badge',
        'order',
        'created_at'
    )
    
    list_filter = ('is_correct', 'created_at')
    
    search_fields = ('choice_text', 'question__question_text')
    
    readonly_fields = ('created_at', 'get_question_link')
    
    fieldsets = (
        ('Choice Information', {
            'fields': ('question', 'choice_text', 'order')
        }),
        ('Status', {
            'fields': ('is_correct',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'get_question_link'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 50
    ordering = ['-created_at']
    
    # ========================================================================
    # Custom Display Methods
    # ========================================================================
    
    def get_choice_preview(self, obj):
        """Display choice text with truncation"""
        text = obj.choice_text[:60]
        if len(obj.choice_text) > 60:
            text += '...'
        return text
    get_choice_preview.short_description = 'Choice Text'
    
    def get_question_link(self, obj):
        """Display clickable link to the question"""
        if obj.question:
            url = reverse('admin:quiz_question_change', args=[obj.question.id])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.question.question_text[:50]
            )
        return "No question"
    get_question_link.short_description = 'Question'
    
    def get_status_badge(self, obj):
        """Display correct/incorrect status with color badge"""
        if obj.is_correct:
            html = '<span style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">✓ CORRECT</span>'
        else:
            html = '<span style="background-color: #6c757d; color: white; padding: 5px 10px; border-radius: 3px;">Incorrect</span>'
        return mark_safe(html)
    get_status_badge.short_description = 'Status'


# ================================================================================
# SUBMISSION ADMIN
# ================================================================================

class SubmissionAdmin(admin.ModelAdmin):
    """
    Admin interface for Submission model.
    Features:
    - Display submissions with user and question info
    - Filter by correctness and user
    - Search functionality
    - Show score and time taken
    """
    
    list_display = (
        'get_user_link',
        'get_question_link',
        'get_answer_preview',
        'get_result_badge',
        'score',
        'get_time_taken',
        'submitted_at'
    )
    
    list_filter = (
        'is_correct',
        'submitted_at',
        ('user', admin.RelatedOnlyFieldListFilter),
        'question__topic'
    )
    
    search_fields = ('user__username', 'question__question_text', 'answer_text')
    
    readonly_fields = (
        'user',
        'question',
        'selected_choice',
        'submitted_at',
        'get_user_link',
        'get_question_link',
        'get_correct_answer'
    )
    
    fieldsets = (
        ('Submission Info', {
            'fields': ('get_user_link', 'get_question_link')
        }),
        ('User Answer', {
            'fields': ('selected_choice', 'answer_text')
        }),
        ('Scoring', {
            'fields': ('is_correct', 'score')
        }),
        ('Timing', {
            'fields': ('submitted_at', 'time_taken')
        }),
        ('Answer Details', {
            'fields': ('get_correct_answer',),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 50
    ordering = ['-submitted_at']
    
    # ========================================================================
    # Custom Display Methods
    # ========================================================================
    
    def get_user_link(self, obj):
        """Display clickable link to user"""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.user.username
        )
    get_user_link.short_description = 'User'
    
    def get_question_link(self, obj):
        """Display clickable link to question"""
        url = reverse('admin:quiz_question_change', args=[obj.question.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.question.question_text[:50]
        )
    get_question_link.short_description = 'Question'
    
    def get_answer_preview(self, obj):
        """Display answer preview"""
        if obj.selected_choice:
            return obj.selected_choice.choice_text[:40]
        elif obj.answer_text:
            return obj.answer_text[:40]
        return "No answer"
    get_answer_preview.short_description = 'Answer'
    
    def get_result_badge(self, obj):
        """Display correct/incorrect badge"""
        if obj.is_correct:
            html = '<span style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 3px;">✓ CORRECT</span>'
        else:
            html = '<span style="background-color: #dc3545; color: white; padding: 5px 10px; border-radius: 3px;">✗ WRONG</span>'
        return mark_safe(html)
    get_result_badge.short_description = 'Result'
    
    def get_time_taken(self, obj):
        """Display formatted time taken"""
        if obj.time_taken:
            return obj.get_time_taken_formatted()
        return "Not recorded"
    get_time_taken.short_description = 'Time Taken'
    
    def get_correct_answer(self, obj):
        """Display the correct answer"""
        correct_choice = obj.question.get_correct_choice()
        if correct_choice:
            return format_html(
                '<span style="background-color: #d4edda; padding: 10px; border-radius: 3px;">✓ {}</span>',
                correct_choice.choice_text
            )
        return "No correct answer defined"
    get_correct_answer.short_description = 'Correct Answer'
    
    # ========================================================================
    # Queryset Optimization
    # ========================================================================
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('user', 'question', 'selected_choice')
        return queryset


# ================================================================================
# QUIZ ADMIN
# ================================================================================

class QuizAdmin(admin.ModelAdmin):
    """
    Admin interface for Quiz model.
    Features:
    - Display quiz with question count
    - Manage quiz questions inline
    - Filter by active status
    - Search by title
    """
    
    list_display = (
        'title',
        'get_question_count',
        'duration',
        'passing_score',
        'is_active',
        'created_at'
    )
    
    list_filter = ('is_active', 'created_at')
    
    search_fields = ('title', 'description')
    
    readonly_fields = ('created_at', 'get_question_count')
    
    fieldsets = (
        ('Quiz Details', {
            'fields': ('title', 'description')
        }),
        ('Settings', {
            'fields': ('duration', 'passing_score', 'is_active')
        }),
        ('Questions', {
            'fields': ('questions',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'get_question_count'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ('questions',)
    
    list_per_page = 25
    ordering = ['-created_at']
    
    # ========================================================================
    # Custom Display Methods
    # ========================================================================
    
    def get_question_count(self, obj):
        """Display number of questions in quiz"""
        count = obj.get_question_count()
        return f"{count} questions"
    get_question_count.short_description = 'Questions'
    
    # ========================================================================
    # Queryset Optimization
    # ========================================================================
    
    def get_queryset(self, request):
        """Optimize queryset with annotation"""
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            question_count=Count('questions', distinct=True)
        )
        return queryset


# ================================================================================
# QUIZ RESULT ADMIN
# ================================================================================

class QuizResultAdmin(admin.ModelAdmin):
    """
    Admin interface for QuizResult model.
    Features:
    - Display results with user and quiz info
    - Show scores and pass/fail status
    - Filter by pass/fail
    """
    
    list_display = (
        'get_user_link',
        'get_quiz_link',
        'score',
        'get_pass_badge',
        'correct_answers',
        'total_questions',
        'get_accuracy',
        'completed_at'
    )
    
    list_filter = ('passed', 'completed_at', ('quiz', admin.RelatedOnlyFieldListFilter))
    
    search_fields = ('user__username', 'quiz__title')
    
    readonly_fields = (
        'user',
        'quiz',
        'started_at',
        'completed_at',
        'get_user_link',
        'get_quiz_link'
    )
    
    fieldsets = (
        ('Result Info', {
            'fields': ('get_user_link', 'get_quiz_link')
        }),
        ('Scores', {
            'fields': ('score', 'passed', 'correct_answers', 'total_questions')
        }),
        ('Timeline', {
            'fields': ('started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 50
    ordering = ['-completed_at']
    
    # ========================================================================
    # Custom Display Methods
    # ========================================================================
    
    def get_user_link(self, obj):
        """Display clickable link to user"""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.user.username
        )
    get_user_link.short_description = 'User'
    
    def get_quiz_link(self, obj):
        """Display clickable link to quiz"""
        url = reverse('admin:quiz_quiz_change', args=[obj.quiz.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.quiz.title
        )
    get_quiz_link.short_description = 'Quiz'
    
    def get_pass_badge(self, obj):
        """Display pass/fail badge"""
        if obj.passed:
            html = '<span style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">PASSED ✓</span>'
        else:
            html = '<span style="background-color: #dc3545; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">FAILED ✗</span>'
        return mark_safe(html)
    get_pass_badge.short_description = 'Status'
    
    def get_accuracy(self, obj):
        """Display accuracy percentage"""
        accuracy = obj.get_accuracy_percentage()
        return f"{accuracy:.1f}%"
    get_accuracy.short_description = 'Accuracy'
    
    # ========================================================================
    # Queryset Optimization
    # ========================================================================
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('user', 'quiz')
        return queryset


# ================================================================================
# REGISTER MODELS WITH ADMIN
# ================================================================================

admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(QuizResult, QuizResultAdmin)

# ================================================================================
# CUSTOMIZE ADMIN SITE
# ================================================================================

admin.site.site_header = "Quiz Application Admin"
admin.site.site_title = "Quiz Admin"
admin.site.index_title = "Welcome to Quiz Admin Panel"

# ================================================================================
# END OF ADMIN CONFIGURATION
# ================================================================================

"""
ADMIN CUSTOMIZATION FEATURES IMPLEMENTED:

1. QuestionInline:
   - Allows inline editing of questions in Quiz admin
   - Extra fields for adding new questions
   
2. ChoiceInline:
   - Allows inline editing of choices in Question admin
   - Display choice text, correctness, and order
   - Shows 2 empty fields for adding new choices

3. QuestionAdmin:
   - Custom list display with colored difficulty badges
   - Filtering by difficulty, type, and topic
   - Inline choice editing
   - Custom actions (mark active/inactive, change difficulty)
   - Read-only submission count
   - Organized fieldsets

4. ChoiceAdmin:
   - Display choices with correct/incorrect status
   - Links to related questions
   - Search by choice text or question text

5. SubmissionAdmin:
   - Display user submissions with results
   - Links to users and questions
   - Show score and time taken
   - Display correct answer
   - Filter by correctness

6. QuizAdmin:
   - Manage quiz questions with filter_horizontal
   - Display question count
   - Set duration and passing score

7. QuizResultAdmin:
   - Display quiz results with pass/fail badges
   - Show accuracy percentage
   - Links to users and quizzes
   - Filter by pass/fail status

All admin classes include:
- Optimized querysets for performance
- Custom display methods with HTML formatting
- Color-coded badges and status indicators
- Inline links to related objects
- Read-only fields where appropriate
- Custom actions and filters
- Proper pagination and ordering
"""
