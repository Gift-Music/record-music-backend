from django.conf.urls import include, url
from django.urls import path

from .views import GoogleLogin, current_user, UserList

app_name = 'accounts'

urlpatterns = [
    path('rest-auth/google/', GoogleLogin.as_view(), name='google_login'),
    path('', UserList.as_view()),
    path('current', current_user),
    # url accounts/registration을 django-rest 라이브러리가 아니라 클라이언트로 연결시킬 예정
]
