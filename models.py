# ================================================================================
# models.py - Django Models for Quiz Application
# Author: Student
# Description: Contains Question, Choice, and Submission models for managing
#              quiz questions, answer choices, and user submissions
# ================================================================================

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

# ================================================================================
# QUESTION MODEL
# ================================================================================

class Question(models.Model):
    """
    Model to store quiz questions.
    
    Fields:
    - id: Auto-generated primary key
    - question_text: The text of the question
    - question_type: Type of question (multiple choice, short answer, etc.)
    - difficulty_level: Difficulty level of the question (easy, medium, hard)
    - topic: The topic/category of the question
    - created_at: Timestamp when the question was created
    - updated_at: Timestamp when the question was last updated
    - is_active: Boolean to indicate if the question is active
    """
    
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice'),
        ('short_answer', 'Short Answer'),
        ('true_false', 'True/False'),
        ('essay', 'Essay'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    question_text = models.TextField(
        help_text="Enter the question text"
    )
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='multiple_choice',
        help_text="Select the type of question"
    )
    difficulty_level = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='medium',
        help_text="Select the difficulty level"
    )
    topic = models.CharField(
        max_length=100,
        help_text="Enter the topic or category of the question"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Automatically set when the question is created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Automatically updated when the question is modified"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indicates if the question is active"
    )
    
    class Meta:
        db_table = 'question'
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['topic']),
            models.Index(fields=['difficulty_level']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        """Return the question text as the string representation"""
        return f"Q{self.id}: {self.question_text[:100]}"
    
    def get_all_choices(self):
        """Get all choices for this question"""
        return self.choice_set.all()
    
    def get_correct_choice(self):
        """Get the correct choice for this question"""
        return self.choice_set.filter(is_correct=True).first()
    
    def get_submission_count(self):
        """Get the number of submissions for this question"""
        return Submission.objects.filter(question=self).count()


# ================================================================================
# CHOICE MODEL
# ================================================================================

class Choice(models.Model):
    """
    Model to store answer choices for questions.
    
    Fields:
    - id: Auto-generated primary key
    - question: Foreign key to Question model
    - choice_text: The text of the choice/answer
    - is_correct: Boolean indicating if this choice is the correct answer
    - order: Order in which to display the choice
    - created_at: Timestamp when the choice was created
    """
    
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        help_text="The question this choice belongs to"
    )
    choice_text = models.TextField(
        help_text="Enter the choice text"
    )
    is_correct = models.BooleanField(
        default=False,
        help_text="Mark if this is the correct answer"
    )
    order = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Order to display this choice (0, 1, 2, etc.)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Automatically set when the choice is created"
    )
    
    class Meta:
        db_table = 'choice'
        verbose_name = 'Choice'
        verbose_name_plural = 'Choices'
        ordering = ['question', 'order']
        unique_together = ['question', 'order']
        indexes = [
            models.Index(fields=['question', 'is_correct']),
            models.Index(fields=['question', 'order']),
        ]
    
    def __str__(self):
        """Return the choice text as the string representation"""
        correct_indicator = " (✓ Correct)" if self.is_correct else ""
        return f"Choice {self.order}: {self.choice_text[:50]}{correct_indicator}"
    
    def mark_as_correct(self):
        """Mark this choice as the correct answer and unmark others"""
        # Unmark other choices for the same question
        Choice.objects.filter(question=self.question).update(is_correct=False)
        # Mark this choice as correct
        self.is_correct = True
        self.save()


# ================================================================================
# SUBMISSION MODEL
# ================================================================================

class Submission(models.Model):
    """
    Model to store user submissions/answers to quiz questions.
    
    Fields:
    - id: Auto-generated primary key
    - user: Foreign key to User model
    - question: Foreign key to Question model
    - selected_choice: Foreign key to Choice model (the answer selected)
    - answer_text: Text answer for short answer/essay questions
    - is_correct: Boolean indicating if the answer is correct
    - score: Score obtained for this submission
    - submitted_at: Timestamp when the answer was submitted
    - time_taken: Time taken to answer the question (in seconds)
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quiz_submissions',
        help_text="The user who made the submission"
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='submissions',
        help_text="The question being answered"
    )
    selected_choice = models.ForeignKey(
        Choice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submissions',
        help_text="The choice selected by the user (for multiple choice)"
    )
    answer_text = models.TextField(
        null=True,
        blank=True,
        help_text="Text answer for short answer or essay questions"
    )
    is_correct = models.BooleanField(
        default=False,
        help_text="Indicates if the submission is correct"
    )
    score = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Score obtained for this submission (0-100)"
    )
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the answer was submitted"
    )
    time_taken = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Time taken to answer (in seconds)"
    )
    
    class Meta:
        db_table = 'submission'
        verbose_name = 'Submission'
        verbose_name_plural = 'Submissions'
        ordering = ['-submitted_at']
        unique_together = ['user', 'question', 'submitted_at']
        indexes = [
            models.Index(fields=['user', 'submitted_at']),
            models.Index(fields=['question', 'is_correct']),
            models.Index(fields=['user', 'question']),
        ]
    
    def __str__(self):
        """Return a string representation of the submission"""
        user_name = self.user.username
        question_id = self.question.id
        status = "✓ Correct" if self.is_correct else "✗ Incorrect"
        return f"{user_name} - Question {question_id}: {status}"
    
    def mark_as_correct(self):
        """Mark this submission as correct"""
        self.is_correct = True
        self.score = 100
        self.save()
    
    def mark_as_incorrect(self):
        """Mark this submission as incorrect"""
        self.is_correct = False
        self.score = 0
        self.save()
    
    def set_score(self, score):
        """Set the score for this submission"""
        if 0 <= score <= 100:
            self.score = score
            self.is_correct = score >= 50  # Assuming 50% is passing
            self.save()
        else:
            raise ValueError("Score must be between 0 and 100")
    
    def get_time_taken_formatted(self):
        """Return time taken in a formatted string"""
        if self.time_taken is None:
            return "Not recorded"
        minutes = self.time_taken // 60
        seconds = self.time_taken % 60
        return f"{minutes}m {seconds}s"


# ================================================================================
# ADDITIONAL MODELS FOR QUIZ MANAGEMENT
# ================================================================================

class Quiz(models.Model):
    """
    Model to group questions into a quiz.
    
    Fields:
    - id: Auto-generated primary key
    - title: Title of the quiz
    - description: Description of the quiz
    - questions: Many-to-many relationship with Question model
    - duration: Duration of the quiz (in minutes)
    - passing_score: Minimum score to pass (0-100)
    - created_at: Timestamp when the quiz was created
    - is_active: Boolean to indicate if the quiz is active
    """
    
    title = models.CharField(
        max_length=200,
        help_text="Enter the title of the quiz"
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Enter a description of the quiz"
    )
    questions = models.ManyToManyField(
        Question,
        related_name='quizzes',
        help_text="Select questions to include in this quiz"
    )
    duration = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(1)],
        help_text="Duration of the quiz in minutes"
    )
    passing_score = models.FloatField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Minimum score to pass (0-100)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the quiz was created"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indicates if the quiz is active"
    )
    
    class Meta:
        db_table = 'quiz'
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizzes'
        ordering = ['-created_at']
    
    def __str__(self):
        """Return the quiz title as the string representation"""
        return self.title
    
    def get_question_count(self):
        """Get the number of questions in this quiz"""
        return self.questions.count()


class QuizResult(models.Model):
    """
    Model to store quiz results for users.
    
    Fields:
    - id: Auto-generated primary key
    - user: Foreign key to User model
    - quiz: Foreign key to Quiz model
    - score: Total score obtained
    - passed: Boolean indicating if the user passed
    - started_at: When the quiz was started
    - completed_at: When the quiz was completed
    - total_questions: Total number of questions
    - correct_answers: Number of correct answers
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quiz_results',
        help_text="The user who took the quiz"
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='results',
        help_text="The quiz that was taken"
    )
    score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Total score obtained"
    )
    passed = models.BooleanField(
        help_text="Indicates if the user passed the quiz"
    )
    started_at = models.DateTimeField(
        help_text="When the quiz was started"
    )
    completed_at = models.DateTimeField(
        help_text="When the quiz was completed"
    )
    total_questions = models.PositiveIntegerField(
        help_text="Total number of questions in the quiz"
    )
    correct_answers = models.PositiveIntegerField(
        help_text="Number of correct answers"
    )
    
    class Meta:
        db_table = 'quiz_result'
        verbose_name = 'Quiz Result'
        verbose_name_plural = 'Quiz Results'
        ordering = ['-completed_at']
        unique_together = ['user', 'quiz', 'completed_at']
    
    def __str__(self):
        """Return a string representation of the quiz result"""
        return f"{self.user.username} - {self.quiz.title}: {self.score}%"
    
    def get_accuracy_percentage(self):
        """Calculate accuracy percentage"""
        if self.total_questions > 0:
            return (self.correct_answers / self.total_questions) * 100
        return 0


# ================================================================================
# SIGNALS FOR AUTOMATIC PROCESSING
# ================================================================================

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

@receiver(post_save, sender=Submission)
def check_submission_correctness(sender, instance, created, **kwargs):
    """
    Signal handler to automatically check if a submission is correct.
    This is called after a Submission is saved.
    """
    if created:  # Only on creation, not on update
        if instance.selected_choice:
            # For multiple choice questions
            instance.is_correct = instance.selected_choice.is_correct
            if instance.is_correct:
                instance.score = 100
            else:
                instance.score = 0
            instance.save(update_fields=['is_correct', 'score'])


# ================================================================================
# QUERYSET METHODS
# ================================================================================

class QuestionQuerySet(models.QuerySet):
    """Custom queryset methods for Question model"""
    
    def active(self):
        """Return only active questions"""
        return self.filter(is_active=True)
    
    def by_difficulty(self, level):
        """Return questions filtered by difficulty level"""
        return self.filter(difficulty_level=level)
    
    def by_topic(self, topic):
        """Return questions filtered by topic"""
        return self.filter(topic=topic)
    
    def multiple_choice(self):
        """Return only multiple choice questions"""
        return self.filter(question_type='multiple_choice')


class QuestionManager(models.Manager):
    """Custom manager for Question model"""
    
    def get_queryset(self):
        """Return custom queryset"""
        return QuestionQuerySet(self.model, using=self._db)
    
    def active(self):
        """Return only active questions"""
        return self.get_queryset().active()
    
    def by_topic(self, topic):
        """Return questions by topic"""
        return self.get_queryset().by_topic(topic)


# ================================================================================
# END OF MODELS
# ================================================================================

"""
USAGE EXAMPLES:

1. Creating a Question:
   question = Question.objects.create(
       question_text="What is 2+2?",
       question_type='multiple_choice',
       difficulty_level='easy',
       topic='Math'
   )

2. Creating Choices:
   Choice.objects.create(
       question=question,
       choice_text="3",
       is_correct=False,
       order=0
   )
   Choice.objects.create(
       question=question,
       choice_text="4",
       is_correct=True,
       order=1
   )

3. Creating a Submission:
   choice = Choice.objects.get(id=1)
   submission = Submission.objects.create(
       user=request.user,
       question=question,
       selected_choice=choice
   )

4. Querying:
   # Get all active questions
   questions = Question.objects.active()
   
   # Get questions by topic
   math_questions = Question.objects.by_topic('Math')
   
   # Get user submissions
   submissions = Submission.objects.filter(user=request.user)
   
   # Get correct submissions
   correct = Submission.objects.filter(is_correct=True)
"""
