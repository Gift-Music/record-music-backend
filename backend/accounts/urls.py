from django.conf.urls.static import static
from django.urls import path

from backend import settings
from . import views, socialloginview

app_name = 'accounts'

urlpatterns = [

    path('login/', views.UserLogin.as_view()),
    path('register/', views.UserRegister.as_view()),
    path('register/activate/', views.UserActivate.as_view(), name='activate_user'),

    path('verify/', views.UserTokenVerify.as_view()),
    path('refresh/', views.UserTokenRefresh.as_view()),

    path('search/<user_id>/', views.Search.as_view(), name='search'),
    path('explore/', views.ExploreUsers.as_view(), name='explore_user'),
    path('<user_id>/profile/', views.UserProfile.as_view(), name='user_profile'),
    path('<user_id>/profile/profileimage/', views.UserProfileImage.as_view(), name='user_profile_images'),
    path('<user_id>/follow/', views.FollowUser.as_view(), name='follow_user'),
    path('<user_id>/unfollow/', views.UnFollowUser.as_view(), name='unfollow_user'),
    path('<user_id>/followers/', views.UserFollowers.as_view(), name='user_followers'),
    path('<user_id>/following/', views.UserFollowing.as_view(), name='user_following'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

social_login_urls = [

    # Facebook
    path('sociallogin/facebook/', socialloginview.fblogin, name='facebook_login'),
    path('sociallogin/facebook/redirect/', socialloginview.fblogin_redirect, name='facebook_login_redirect'),

    # Google
    path('sociallogin/google/', socialloginview.gglogin, name='google_login'),
    path('sociallogin/google/redirect/', socialloginview.gglogin_redirect, name='google_login_redirect'),

]

urlpatterns += social_login_urls
