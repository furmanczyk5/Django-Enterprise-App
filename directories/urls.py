from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'^members/directory/$', views.DirectoryView.as_view(), kwargs={"code":"DIRECTORY_MEMBER"}),
    url(r'^members/directory/aicp/$', views.DirectoryView.as_view(), kwargs={"code":"DIRECTORY_AICP"}),
    url(r'^members/directory/pas/$', views.PASDirectoryView.as_view(), kwargs={"code":"DIRECTORY_PAS"}),

    url(r'^chapters/alaska/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_CHAPT_AK"}),
    url(r'^chapters/kansas/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_CHAPT_KS"}),
    url(r'^chapters/nebraska/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_CHAPT_NE"}),
    #url(r'^chapters/maryland/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_CHAPT_MD"}),
    url(r'^chapters/virginia/directory/form/', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_CHAPT_VA"}),
    url(r'^chapters/missouri/directory/form/', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_CHAPT_MO"}),
    url(r'^divisions/cityplanning/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_CITY_PLAN"}),
    url(r'^divisions/latinos/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_LAP"}),
    url(r'^divisions/smalltown/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_SMALL_TOWN"}),
    url(r'^divisions/transportation/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_TRANS"}),
    url(r'^divisions/urbandesign/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_URBAN_DES"}),
    url(r'^divisions/planningandwomen/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_WOMEN"}),
    url(r'^divisions/planningandlaw/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_LAW"}),
    url(r'^divisions/newurbanism/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_NEW_URB"}),
    url(r'^divisions/blackcommunity/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_PLAN_BLACK"}),
    url(r'^divisions/privatepractice/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_PRIVATE"}),
    url(r'^divisions/sustainable/directory/form/', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_SCD"}),
    url(r'^divisions/countyplanning/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_CPD"}),
    url(r'^divisions/economic/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_ECON"}),
    url(r'^divisions/federal/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_FED_PLAN"}),
    url(r'^divisions/galip/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_GALIP"}),
    url(r'^divisions/hazardmitigation/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_HMDR"}),
    url(r'^divisions/housing/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_HOUSING"}),
    url(r'^divisions/tech/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_INFO_TECH"}),
    url(r'^divisions/regional/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_INTER_GOV"}),
    url(r'^divisions/international/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_INTL"}),
    url(r'^divisions/environment/directory/form/$', views.DivisionChapterDirectoryView.as_view(), kwargs={"code":"DIRECTORY_ENVIRON"}),
    url(r'^chapters/pdo/$', views.PDOsView.as_view(), kwargs={"code":"PDO_LIST"}),

    url(r'^members/resume-search/$', views.ResumeSearchView.as_view()),

    # url(r'^leadership/committees/(?P<code>.+)/$', views.RosterView.as_view() ),
    # url(r'^divisions/cityplanning/leadership/$', views.RosterView.as_view(), kwargs={"code":"LEADERSHIP_CITYPLAN"}),

]
