from django.urls import path
from rest_auth.views import LogoutView

from . import views

app_name = 'accounts'

urlpatterns = [
    path('rest-auth/google/', views.GoogleLogin.as_view(), name='google_login'),

    path('login/', views.UserLogin.as_view()),
    path('logout/', LogoutView.as_view()),
    path('register/', views.UserRegister.as_view()),

    path('verify/', views.UserTokenVerify.as_view()),
    path('refresh/', views.UserTokenRefresh.as_view()),

    path('search/', views.Search.as_view(), name='search'),
    path('explore/', views.ExploreUsers.as_view(), name='explore_user'),
    path('<userid>/', views.UserProfile.as_view(), name='user_profile'),
    path('<userid>/follow/', views.FollowUser.as_view(), name='follow_user'),
    path('<userid>/unfollow/', views.UnFollowUser.as_view(), name='unfollow_user'),
    path('<userid>/followers/', views.UserFollowers.as_view(), name='user_followers'),
    path('<userid>/following/', views.UserFollowing.as_view(), name='user_following'),
]
