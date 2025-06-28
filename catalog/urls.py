from django.urls import path
from . import views

urlpatterns = [
    path("curriculum/", views.curriculum_index, name="curriculum_index"),

    path("curriculum/programme/add/",     views.programme_create,  name="programme_add"),
    path("curriculum/programme/<int:pk>/", views.programme_edit,   name="programme_edit"),

    path("curriculum/major/add/",         views.major_create,      name="major_add"),
    path("curriculum/major/<int:pk>/",    views.major_edit,        name="major_edit"),

    path("curriculum/subject/add/",       views.subject_create,    name="subject_add"),
    path("curriculum/subject/<int:pk>/",  views.subject_edit,      name="subject_edit"),

    path("curriculum/trimester/add/",     views.trimester_create,  name="trimester_add"),

    path("curriculum/offering/add/",      views.offering_create,   name="offering_add"),
]
