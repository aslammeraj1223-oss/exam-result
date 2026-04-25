from django.urls import path
from . import views

app_name = "onlinecourse"

urlpatterns = [
    path(route="", view=views.index, name="index"),
    path(route="registration/", view=views.registration_request, name="registration"),
    path(route="login/", view=views.login_request, name="login"),
    path(route="logout/", view=views.logout_request, name="logout"),
    path(route="course/<int:course_id>/enroll/", view=views.enroll, name="enroll"),
    path(route="course/<int:course_id>/", view=views.course_details, name="course_details"),
    # Submit exam path
    path(route="course/<int:course_id>/submit/", view=views.submit, name="submit"),
    # Show exam result path
    path(
        route="course/<int:course_id>/submission/<int:submission_id>/result/",
        view=views.show_exam_result,
        name="show_exam_result",
    ),
]
