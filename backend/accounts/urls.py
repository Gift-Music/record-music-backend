from django.conf.urls import include, url
from django.urls import path

from . import views
from rest_framework_jwt.views import refresh_jwt_token, verify_jwt_token

app_name = 'accounts'

urlpatterns = [
    path('rest-auth/google/', views.GoogleLogin.as_view(), name='google_login'),
    path('current', views.current_user),

    path('login/', views.UserLogin.as_view()),
    path('logout/', views.UserLogout.as_view()),
    path('registration/', views.UserRegister.as_view()),

    path('verify/', views.UserTokenVerify.as_view()),
    path('refresh/', refresh_jwt_token),

    url(r'^search/$', views.Search.as_view(), name='search'),
    url(r'^explore/$', views.ExploreUsers.as_view(), name='explore_user'),
    url(r'^(?P<userid>\w+)/$', views.UserProfile.as_view(), name='user_profile'),
    url(r'^(?P<userid>\d+)/follow/$', views.FollowUser.as_view(), name='follow_user'),
    url(r'^(?P<userid>\d+)/unfollow/$', views.UnFollowUser.as_view(), name='unfollow_user'),
    url(r'^(?P<userid>\w+)/followers/$', views.UserFollowers.as_view(), name='user_followers'),
    url(r'^(?P<userid>\w+)/following/$', views.UserFollowing.as_view(), name='user_following'), # 로그인 되어 있는 유저가 팔로우한 다른 유저목록
]
