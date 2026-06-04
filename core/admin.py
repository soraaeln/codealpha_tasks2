from django.contrib import admin

from .models import Comment, FUsers, InboxMessage, Like, PendingSignup, Post, PostShare, Share


@admin.register(FUsers)
class FUsersAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "is_verified", "created_at")
    search_fields = ("username", "email", "bio", "location")
    list_filter = ("is_verified", "created_at")
    ordering = ("-created_at",)


@admin.register(PendingSignup)
class PendingSignupAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "code", "is_used", "created_at")
    search_fields = ("username", "email", "code")
    list_filter = ("is_used", "created_at")
    ordering = ("-created_at",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("author", "created_at")
    search_fields = ("author__username", "caption")


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "created_at")
    search_fields = ("user__username", "post__caption")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "post", "created_at")
    search_fields = ("author__username", "post__caption", "body")


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "created_at")
    search_fields = ("user__username", "post__caption")


@admin.register(PostShare)
class PostShareAdmin(admin.ModelAdmin):
    list_display = ("sender", "recipient", "post", "created_at")
    search_fields = ("sender__username", "recipient__username", "post__caption")


@admin.register(InboxMessage)
class InboxMessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "recipient", "post", "is_read", "created_at")
    search_fields = ("sender__username", "recipient__username", "post__caption")
    list_filter = ("is_read", "created_at")
