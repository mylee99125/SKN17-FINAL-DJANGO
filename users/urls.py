from django.urls import path
from . import views 

app_name = 'users'

urlpatterns = [
    # 메인
    path('', views.index, name='index'),

    # 회원가입
    path('email/send-code/', views.send_verification_code, name='send_code'),
    path('email/verify-code/', views.verify_code, name='verify_code'),
    path('password', views.save_password_temp, name='password'),
    path('signup', views.complete_signup, name='signup'),

    # 로그인/아웃
    path('login', views.login_user, name='login'),
    path("logout", views.logout, name="logout"),

    # 비밀번호 찾기
    path("password_reset", views.send_reset_code, name="password_reset"),
    path("password_reset/verify", views.verify_reset_code, name="password_reset_verify"),
    path("password_reset/final", views.reset_password, name="password_reset_final"),

    # 사용자 환경설정
    path("setting", views.setting, name="setting"),
    path("update_team", views.update_team, name="update_team"),
    path("update_password", views.update_password, name="update_password"),
    path("delete_account", views.delete_account, name="delete_account")
]