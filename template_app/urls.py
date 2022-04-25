from django.conf.urls import url

from template_app import views

urlpatterns = [
    url(r"^sandbox/publications/$", views.Publications.as_view(), name="publications" ),
    url(r"^sandbox/conferences-and-meetings/$", views.ConferencesAndMeetings.as_view(), name="conferences-and-meetings" ),
    url(r"^sandbox/directory-page/$", views.DirectoryPage.as_view(), name="directory-page" ),
    url(r"^sandbox/pattern-library/1/$", views.PatternLibrary1.as_view(), name="pattern-library-1" ),
    url(r"^sandbox/pattern-library/2/$", views.PatternLibrary2.as_view(), name="pattern-library-2" ),
    url(r"^sandbox/pattern-library/3/$", views.PatternLibrary3.as_view(), name="pattern-library-3" ),
    url(r"^sandbox/pattern-library/4/$", views.PatternLibrary4.as_view(), name="pattern-library-4" ),
    url(r"^sandbox/legacy-content/1/$", views.LegacyContent1.as_view(), name="legacy-content-1" ),
    url(r"^sandbox/legacy-content/2/$", views.LegacyContent2.as_view(), name="legacy-content-2" ),
    url(r"^sandbox/legacy-content/3/$", views.LegacyContent3.as_view(), name="legacy-content-3" ),
    url(r"^sandbox/legacy-content/4/$", views.LegacyContent4.as_view(), name="legacy-content-4" ),
    url(r"^sandbox/new-content/$", views.NewContent.as_view(), name="new-content" ),
    url(r"^sandbox/interim-content/$", views.InterimContent.as_view(), name="interim-content" ),
    url(r"^sandbox/cart/$", views.Cart.as_view(), name="cart" ),
    url(r"^sandbox/order-confirmation/$", views.OrderConfirmation.as_view(), name="order-confirmation" ),
    url(r"^sandbox/search/$", views.Search.as_view(), name="search" ),
    url(r"^sandbox/home/$", views.Home.as_view(), name="home" ),
    url(r"^sandbox/planning-magazine-issue/$", views.PlanningMagazineIssue.as_view(), name="home" ),
    url(r'^sandbox/forms/test/$', views.FormTestView.as_view(), name="form_test"),
    url(r'^sandbox/forms/account/$', views.AccountFormView.as_view(), name="account_form"),
    url(r"^sandbox/pattern-library/5/$", views.PatternLibrary5.as_view(), name="pattern-library-5" ),
    url(r"^sandbox/pattern-library/linked-images/$", views.PatternLibraryLinkedImages.as_view(), name="pattern-library-linked-images" ),

    url(r"^prototype/join/student/account-information/$", views.PrototypeJoinStudentAccountInformationView.as_view(), name="prototype_join_student_account_information" ),
    url(r"^prototype/join/student/student-information/$", views.PrototypeJoinStudentInformationView.as_view(), name="prototype_join_student_information" ),
    url(r"^prototype/join/student/enhance-membership/$", views.PrototypeJoinAddDivisionsAndSubscriptionsView.as_view(), name="prototype_join_student_enhance_membership" ),
    # Conference
    url(r"^sandbox/pattern-library-conference/1/$", views.ConferencePatternLibrary1.as_view(), name="pattern-library-conference-1" ),
    url(r"^sandbox/pattern-library-conference/2/$", views.ConferencePatternLibrary2.as_view(), name="pattern-library-conference-2" ),
    url(r"^sandbox/pattern-library-conference/3/$", views.ConferencePatternLibrary3.as_view(), name="pattern-library-conference-3" ),
    url(r"^sandbox/pattern-library-conference/4/$", views.ConferencePatternLibrary4.as_view(), name="pattern-library-conference-4" ),
    url(r"^sandbox/pattern-library-conference/5/$", views.ConferencePatternLibrary5.as_view(), name="pattern-library-conference-5" ),
    url(r"^sandbox/pattern-library-conference/6/$", views.ConferencePatternLibrary6.as_view(), name="pattern-library-conference-6" ),
    url(r"^sandbox/pattern-library-conference/session-detail/$", views.ConferencePatternLibrarySessionDetail.as_view(), name="pattern-library-conference-session-detail" ),
    url(r"^sandbox/pattern-library-conference/sponsorship/$", views.ConferencePatternLibrarySponsorship.as_view(), name="pattern-library-conference-sponsorship" ),
    url(r"^sandbox/conference/home/$", views.ConferenceHome.as_view(), name="conference-home" ),
    url(r"^sandbox/conference/tracks/$", views.ConferenceTracks.as_view(), name="conference-tracks" ),
    url(r"^sandbox/conference/content/$", views.ConferenceContent.as_view(), name="conference-content" ),
    # Plannning Magazine
    url(r"^sandbox/planning-magazine/landing-page/$", views.PlanningMagazineLandingPage.as_view(), name="planning-magazine-landing-page" ),
    url(r"^sandbox/planning-magazine/type-landing-page/$", views.PlanningMagazineTypeLandingPage.as_view(), name="planning-magazine-type-landing-page" ),
    url(r"^sandbox/planning-magazine/article-page/$", views.PlanningMagazineArticlePage.as_view(), name="planning-magazine-article-page" ),

    url(r"^prototype/(?P<template_name>.+)$", views.PrototypeTemplateView.as_view(), name="prototype" )

]
