from django.urls import path

from . import views

urlpatterns = [
    path("", views.feed, name="feed"),
    path("login/", views.login_page, name="login"),
    path("signup/", views.signup_page, name="signup"),
    path("verify/", views.verify_page, name="verify"),
    path("resend-otp/", views.resend_otp, name="resend_otp"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("reset-password/", views.reset_password, name="reset_password"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("post/create/", views.create_post, name="create_post"),
    path("post/<int:post_id>/edit/", views.edit_post, name="edit_post"),
    path("post/<int:post_id>/delete/", views.delete_post, name="delete_post"),
    path("messages/<str:username>/", views.chat_thread, name="chat_thread"),
    path("messages/<int:message_id>/delete/", views.delete_message, name="delete_message"),
    path("messages/", views.inbox, name="messages"),
    path("u/<str:username>/", views.profile_view, name="profile"),
    path("u/<str:username>/follow/", views.toggle_follow, name="toggle_follow"),
    path("posts/<int:post_id>/like/", views.toggle_like, name="toggle_like"),
    path("posts/<int:post_id>/comment/", views.add_comment, name="add_comment"),
    path("comments/<int:comment_id>/delete/", views.delete_comment, name="delete_comment"),
    path("posts/<int:post_id>/share/", views.toggle_share, name="toggle_share"),
    path("posts/<int:post_id>/share-to-user/", views.share_post_to_user, name="share_post_to_user"),
]
