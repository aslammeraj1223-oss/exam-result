from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import logging

from .models import Course, Enrollment, Question, Choice, Submission

logger = logging.getLogger(__name__)


def registration_request(request):
    context = {}
    if request.method == "GET":
        return render(request, "onlinecourse/user_registration_bootstrap.html", context)
    elif request.method == "POST":
        from django.contrib.auth.models import User
        import django.contrib.auth as auth
        username = request.POST["username"]
        password = request.POST["psw"]
        first_name = request.POST["firstname"]
        last_name = request.POST["lastname"]
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except Exception:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password,
            )
            auth.login(request, user)
            return redirect("onlinecourse:index")
        else:
            context["message"] = "User already exists."
            return render(
                request,
                "onlinecourse/user_registration_bootstrap.html",
                context,
            )


def login_request(request):
    context = {}
    if request.method == "POST":
        import django.contrib.auth as auth
        username = request.POST["username"]
        password = request.POST["psw"]
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect("onlinecourse:index")
        else:
            context["message"] = "Invalid username or password."
            return render(request, "onlinecourse/user_login_bootstrap.html", context)
    else:
        return render(request, "onlinecourse/user_login_bootstrap.html", context)


def logout_request(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect("onlinecourse:index")


def index(request):
    courses = Course.objects.order_by("-total_enrollment")[:10]
    context = {}
    if request.user.is_authenticated:
        context["courses_enrolled"] = courses.filter(users=request.user)
        context["courses_not_enrolled"] = courses.exclude(users=request.user)
    else:
        context["courses"] = courses
    return render(request, "onlinecourse/course_list_bootstrap.html", context)


@login_required
def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    is_enrolled = Enrollment.objects.filter(user=user, course=course).exists()
    if not is_enrolled and user.is_authenticated:
        Enrollment.objects.create(user=user, course=course, mode=0)
        course.total_enrollment += 1
        course.save()
    return HttpResponseRedirect(
        reverse("onlinecourse:course_details", args=(course.id,))
    )


def course_details(request, course_id):
    context = {}
    course = get_object_or_404(Course, pk=course_id)
    context["course"] = course
    if request.user.is_authenticated:
        try:
            context["enrollment"] = Enrollment.objects.get(
                user=request.user, course=course
            )
        except Enrollment.DoesNotExist:
            pass
    return render(request, "onlinecourse/course_details_bootstrap.html", context)


@login_required
def submit(request, course_id):
    # Retrieve the current logged-in user and the course
    user = request.user
    course = get_object_or_404(Course, pk=course_id)

    # Retrieve the enrollment for this user and course
    enrollment = get_object_or_404(Enrollment, user=user, course=course)

    # Create a new Submission object linked to the enrollment
    submission = Submission.objects.create(enrollment=enrollment)

    # Collect all selected choice IDs from the POST data
    submitted_answers = []
    for key in request.POST:
        if key.startswith("choice"):
            for value in request.POST.getlist(key):
                submitted_answers.append(int(value))

    # Add the selected choices to the submission
    chosen_choices = Choice.objects.filter(id__in=submitted_answers)
    submission.choices.set(chosen_choices)
    submission.save()

    # Redirect to show_exam_result with course_id and submission_id
    return HttpResponseRedirect(
        reverse("onlinecourse:show_exam_result", args=(course_id, submission.id))
    )


def show_exam_result(request, course_id, submission_id):
    # Retrieve the course and submission objects
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)

    # Get the list of choice IDs the learner selected
    choices = submission.choices.all()
    selected_ids = list(choices.values_list("id", flat=True))

    # Calculate the total score by checking each question
    total_score = 0
    for question in course.question_set.all():
        if question.is_get_score(selected_ids):
            total_score += question.grade

    # Build context and render the exam result template
    context = {
        "course": course,
        "submission": submission,
        "choices": choices,
        "selected_ids": selected_ids,
        "total_score": total_score,
    }
    return render(request, "onlinecourse/exam_result_bootstrap.html", context)
