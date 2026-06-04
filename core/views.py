import random

from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .models import Comment, FUsers, InboxMessage, Like, PendingSignup, Post, PostShare, Share


def get_current_user(request):
    user_id = request.session.get("fleek_user_id")
    if not user_id:
        return None
    try:
        return FUsers.objects.get(id=user_id)
    except FUsers.DoesNotExist:
        request.session.pop("fleek_user_id", None)
        return None


def auth_required(view_func):
    def wrapper(request, *args, **kwargs):
        current_user = get_current_user(request)
        if current_user is None:
            return redirect("login")
        request.fleek_user = current_user
        return view_func(request, *args, **kwargs)

    return wrapper


def generate_otp():
    return str(random.randint(100000, 999999))


def redirect_back_to_post(request, post_id):
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"
    if "#" in next_url:
        next_url = next_url.split("#", 1)[0]
    return redirect(f"{next_url}#post-{post_id}")


def mark_message_threads_read(messages_qs):
    messages_qs.update(is_read=True)


def login_page(request):
    if get_current_user(request):
        return redirect("feed")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        try:
            user = FUsers.objects.get(username=username)
        except FUsers.DoesNotExist:
            user = None
        if user and not user.is_verified:
            messages.error(request, "Please verify your account using the OTP sent to your email.")
            return render(request, "Fleek/login.html")
        if user and check_password(password, user.password):
            request.session["fleek_user_id"] = user.id
            return redirect("feed")
        messages.error(request, "Invalid username or password.")
    return render(request, "Fleek/login.html")


def signup_page(request):
    if get_current_user(request):
        return redirect("feed")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("password2", "")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
        elif FUsers.objects.filter(username=username).exists():
            messages.error(request, "That username is already taken.")
        elif FUsers.objects.filter(email=email).exists():
            messages.error(request, "That email is already registered.")
        else:
            PendingSignup.objects.filter(email__iexact=email, is_used=False).update(is_used=True)
            code = generate_otp()
            PendingSignup.objects.create(
                username=username,
                email=email,
                password_hash=make_password(password),
                code=code,
            )
            send_mail(
                "Your OTP Code",
                f"Your OTP is: {code}",
                "yourgmail@gmail.com",
                [email],
                fail_silently=True,
            )
            request.session["pending_email"] = email
            messages.success(request, "OTP sent to your email. Please verify your account.")
            return redirect("verify")
    return render(request, "Fleek/signup.html")


def verify_page(request):
    if request.method == "POST":
        email = request.POST.get("email")
        code = request.POST.get("code")
        try:
            pending = PendingSignup.objects.get(email=email, code=code, is_used=False)
        except PendingSignup.DoesNotExist:
            return render(request, "Fleek/verify.html", {"error": "Invalid OTP"})

        user = FUsers.objects.create(
            username=pending.username,
            email=pending.email,
            password=pending.password_hash,
            is_verified=True,
        )
        pending.is_used = True
        pending.save()
        request.session["fleek_user_id"] = user.id
        request.session.pop("pending_email", None)
        return redirect("feed")

    return render(request, "Fleek/verify.html", {"email": request.session.get("pending_email", "")})


def resend_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            pending = PendingSignup.objects.get(email=email, is_used=False)
        except PendingSignup.DoesNotExist:
            return render(request, "Fleek/verify.html", {"error": "No pending signup found"})

        new_code = generate_otp()
        pending.code = new_code
        pending.created_at = timezone.now()
        pending.save()
        send_mail("Your New OTP Code", f"Your new OTP is: {new_code}", "yourgmail@gmail.com", [email], fail_silently=True)
        return render(request, "Fleek/verify.html", {"error": "New OTP sent!", "email": email})


def forgot_password(request):
    if get_current_user(request):
        return redirect("feed")
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        try:
            user = FUsers.objects.get(email=email)
        except FUsers.DoesNotExist:
            messages.error(request, "No account found with that email.")
        else:
            code = generate_otp()
            request.session["reset_email"] = email
            request.session["reset_code"] = code
            request.session["reset_code_sent_at"] = timezone.now().isoformat()
            send_mail(
                "Your Password Reset Code",
                f"Your password reset code is: {code}",
                "yourgmail@gmail.com",
                [email],
                fail_silently=True,
            )
            return redirect("reset_password")
    return render(request, "Fleek/forgot_password.html")


def reset_password(request):
    if get_current_user(request):
        return redirect("feed")
    reset_email = request.session.get("reset_email", "")
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        code = request.POST.get("code", "").strip()
        new_password = request.POST.get("new_password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if email != request.session.get("reset_email"):
            messages.error(request, "Reset session expired. Please request a new code.")
        elif code != request.session.get("reset_code"):
            messages.error(request, "Invalid reset code.")
        elif new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
        else:
            user = FUsers.objects.get(email=email)
            user.password = make_password(new_password)
            user.save()
            request.session.pop("reset_email", None)
            request.session.pop("reset_code", None)
            request.session.pop("reset_code_sent_at", None)
            messages.success(request, "Password reset successfully. Please log in.")
            return redirect("login")

    return render(request, "Fleek/reset_password.html", {"email": reset_email})


@auth_required
def feed(request):
    current_user = request.fleek_user
    search_query = request.GET.get("q", "").strip()

    visible_authors = FUsers.objects.all()
    posts = (
        Post.objects.filter(author__in=visible_authors)
        .select_related("author")
        .prefetch_related("likes", "post_shares", "comments__author")
        .annotate(
            likes_count=Count("likes", distinct=True),
            comments_count=Count("comments", distinct=True),
            shares_count=Count("post_shares", distinct=True),
        )
    )
    if search_query:
        posts = posts.filter(Q(caption__icontains=search_query) | Q(author__username__icontains=search_query))
    people = FUsers.objects.exclude(id=current_user.id)
    if search_query:
        people = people.filter(
            Q(username__icontains=search_query)
            | Q(nickname__icontains=search_query)
            | Q(bio__icontains=search_query)
        )
    followers = current_user.followers.all().order_by("username")
    following_count = FUsers.objects.filter(followers=current_user).count()
    added_posts = Post.objects.filter(author=current_user).order_by("-created_at")[:5]
    liked_post_ids = set(Like.objects.filter(user=current_user, post__in=posts).values_list("post_id", flat=True))
    shared_post_ids = set(
        PostShare.objects.filter(sender=current_user, post__in=posts).values_list("post_id", flat=True)
    )
    return render(
        request,
        "Fleek/home.html",
        {
            "current_user": current_user,
            "posts": posts,
            "people": people,
            "followers": followers,
            "added_posts": added_posts,
            "search_query": search_query,
            "following_count": following_count,
            "followers_count": followers.count(),
            "liked_post_ids": liked_post_ids,
            "shared_post_ids": shared_post_ids,
            "share_people": people,
        },
    )


def get_message_conversations(current_user):
    return FUsers.objects.filter(
        Q(sent_messages__recipient=current_user) | Q(received_messages__sender=current_user)
    ).distinct().order_by("username")


@auth_required
def inbox(request):
    current_user = request.fleek_user
    messages_qs = InboxMessage.objects.filter(recipient=current_user).select_related("sender", "post", "post__author")
    if request.method == "POST":
        mark_message_threads_read(messages_qs)
        return redirect("messages")
    unread_count = messages_qs.filter(is_read=False).count()
    conversations = get_message_conversations(current_user)
    return render(
        request,
        "Fleek/messages.html",
        {
            "current_user": current_user,
            "conversations": conversations,
            "unread_count": unread_count,
        },
    )


@auth_required
def chat_thread(request, username):
    current_user = request.fleek_user
    thread_user = get_object_or_404(FUsers, username=username)
    if thread_user == current_user:
        return redirect("messages")

    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        editing_message_id = request.POST.get("editing_message_id", "").strip()
        thread_url = reverse("chat_thread", kwargs={"username": thread_user.username})
        if editing_message_id:
            message = get_object_or_404(
                InboxMessage.objects.select_related("sender", "recipient"),
                id=editing_message_id,
                sender=current_user,
            )
            if not message.body:
                messages.error(request, "Only text messages can be edited.")
                return redirect("chat_thread", username=thread_user.username)
            if body:
                message.body = body
                message.save(update_fields=["body"])
                messages.success(request, "Message updated.")
            else:
                messages.error(request, "Message cannot be empty.")
            return redirect(f"{thread_url}#chat-composer")
        if body:
            InboxMessage.objects.create(sender=current_user, recipient=thread_user, body=body)
        return redirect(f"{thread_url}#chat-composer")

    conversations = get_message_conversations(current_user)
    thread_messages = (
        InboxMessage.objects.filter(
            Q(sender=current_user, recipient=thread_user) | Q(sender=thread_user, recipient=current_user)
        )
        .select_related("sender", "recipient", "post", "post__author")
        .order_by("created_at")
    )
    thread_messages.filter(sender=thread_user, recipient=current_user, is_read=False).update(is_read=True)
    unread_count = InboxMessage.objects.filter(recipient=current_user, is_read=False).count()

    return render(
        request,
        "Fleek/messages.html",
        {
            "current_user": current_user,
            "conversations": conversations,
            "thread_user": thread_user,
            "thread_messages": thread_messages,
            "unread_count": unread_count,
        },
    )


@auth_required
def edit_message(request, message_id):
    current_user = request.fleek_user
    message = get_object_or_404(
        InboxMessage.objects.select_related("sender", "recipient"),
        id=message_id,
    )
    if message.sender != current_user:
        return redirect("messages")
    return redirect("chat_thread", username=message.recipient.username)


@auth_required
def delete_message(request, message_id):
    current_user = request.fleek_user
    message = get_object_or_404(
        InboxMessage.objects.select_related("sender", "recipient"),
        id=message_id,
    )
    if message.sender != current_user:
        return redirect("messages")
    if request.method == "POST":
        partner_username = message.recipient.username
        message.delete()
        messages.success(request, "Message deleted.")
        return redirect("chat_thread", username=partner_username)
    return redirect("chat_thread", username=message.recipient.username)


@auth_required
def create_post(request):
    current_user = request.fleek_user
    media_position_x = 50
    media_position_y = 50
    if request.method == "POST":
        caption = request.POST.get("caption", "").strip()
        image_url = request.POST.get("image_url", "").strip()
        media_file = request.FILES.get("media_file")
        media_position_x = int(request.POST.get("media_position_x", 50))
        media_position_y = int(request.POST.get("media_position_y", 50))
        if media_file or image_url:
            post = Post(author=current_user, caption=caption)
            if media_file:
                if media_file.content_type.startswith("video/"):
                    post.video_file = media_file
                    post.image_file = None
                    post.media_position_x = 50
                    post.media_position_y = 50
                else:
                    post.image_file = media_file
                    post.video_file = None
                    post.image_url = ""
                    post.media_position_x = media_position_x
                    post.media_position_y = media_position_y
            else:
                post.image_url = image_url
                post.media_position_x = media_position_x
                post.media_position_y = media_position_y
            post.save()
            messages.success(request, "Post published.")
            return redirect("feed")
        messages.error(request, "Please add an image, video, or image URL before publishing.")

    return render(
        request,
        "Fleek/create_post.html",
        {
            "current_user": current_user,
            "form_title": "Create a post",
            "form_description": "Share a photo or video. Media is required for every post.",
            "submit_label": "Publish post",
            "caption": "",
            "image_url": "",
            "media_position_x": media_position_x,
            "media_position_y": media_position_y,
        },
    )


@auth_required
def edit_post(request, post_id):
    current_user = request.fleek_user
    post = get_object_or_404(Post, id=post_id)
    if post.author != current_user:
        return redirect("feed")

    if request.method == "POST":
        caption = request.POST.get("caption", "").strip()
        image_url = request.POST.get("image_url", "").strip()
        media_file = request.FILES.get("media_file")
        media_position_x = int(request.POST.get("media_position_x", post.media_position_x))
        media_position_y = int(request.POST.get("media_position_y", post.media_position_y))
        if caption or media_file or image_url:
            post.caption = caption
            if media_file:
                if media_file.content_type.startswith("video/"):
                    if post.image_file:
                        post.image_file.delete(save=False)
                    post.video_file = media_file
                    post.image_file = None
                    post.media_position_x = 50
                    post.media_position_y = 50
                else:
                    if post.video_file:
                        post.video_file.delete(save=False)
                    post.image_file = media_file
                    post.video_file = None
                    post.image_url = ""
                    post.media_position_x = media_position_x
                    post.media_position_y = media_position_y
            elif image_url:
                if post.image_file:
                    post.image_file.delete(save=False)
                if post.video_file:
                    post.video_file.delete(save=False)
                post.image_file = None
                post.video_file = None
                post.image_url = image_url
                post.media_position_x = media_position_x
                post.media_position_y = media_position_y
            elif not post.image_file and not post.video_file and not post.image_url:
                messages.error(request, "Please attach an image, video, or image URL before saving.")
                return render(
                    request,
                    "Fleek/create_post.html",
                    {
                        "current_user": current_user,
                        "form_title": "Edit post",
                        "form_description": "Update your caption or image URL.",
                        "submit_label": "Save changes",
                        "caption": caption,
                        "image_url": image_url,
                        "media_position_x": media_position_x,
                        "media_position_y": media_position_y,
                    },
                )
            post.save()
            messages.success(request, "Post updated.")
            return redirect("feed")
        messages.error(request, "Please add an image, video, or image URL before saving.")

    return render(
        request,
        "Fleek/create_post.html",
        {
            "current_user": current_user,
            "form_title": "Edit post",
            "form_description": "Update your caption or image URL.",
            "submit_label": "Save changes",
            "caption": post.caption,
            "image_url": post.image_url,
            "media_position_x": post.media_position_x,
            "media_position_y": post.media_position_y,
            "media_src": post.media_src,
            "media_is_video": post.is_video,
        },
    )


@auth_required
def delete_post(request, post_id):
    current_user = request.fleek_user
    post = get_object_or_404(Post, id=post_id)
    if post.author != current_user:
        return redirect("feed")
    if request.method == "POST":
        post.delete()
        messages.success(request, "Post deleted.")
        next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"
        return redirect(next_url)
    return redirect("feed")


@auth_required
def share_post_to_user(request, post_id):
    current_user = request.fleek_user
    post = get_object_or_404(Post, id=post_id)
    recipient_id = request.POST.get("recipient_id")
    recipient = get_object_or_404(FUsers, id=recipient_id)
    if recipient != current_user:
        PostShare.objects.get_or_create(post=post, sender=current_user, recipient=recipient)
        InboxMessage.objects.get_or_create(sender=current_user, recipient=recipient, post=post)
        messages.success(request, f"Shared to {recipient.username}.")
    else:
        messages.error(request, "You can't share a post to yourself.")
    return redirect_back_to_post(request, post_id)


@auth_required
def profile_view(request, username):
    current_user = request.fleek_user
    profile_user = get_object_or_404(FUsers, username=username)
    posts = (
        Post.objects.filter(author=profile_user)
        .select_related("author")
        .prefetch_related("likes", "post_shares", "comments__author")
        .annotate(
            likes_count=Count("likes", distinct=True),
            comments_count=Count("comments", distinct=True),
            shares_count=Count("post_shares", distinct=True),
        )
    )
    is_following = profile_user.followers.filter(id=current_user.id).exists()
    liked_post_ids = set(Like.objects.filter(user=current_user, post__in=posts).values_list("post_id", flat=True))
    shared_post_ids = set(
        PostShare.objects.filter(sender=current_user, post__in=posts).values_list("post_id", flat=True)
    )
    followers_list = profile_user.followers.all().order_by("username")
    following_list = FUsers.objects.filter(followers=profile_user).order_by("username")
    return render(
        request,
        "Fleek/profile.html",
        {
            "current_user": current_user,
            "profile_user": profile_user,
            "posts": posts,
            "is_following": is_following,
            "followers_count": followers_list.count(),
            "following_count": following_list.count(),
            "followers_list": followers_list,
            "following_list": following_list,
            "liked_post_ids": liked_post_ids,
            "shared_post_ids": shared_post_ids,
            "share_people": FUsers.objects.exclude(id=current_user.id),
        },
    )


@auth_required
def toggle_follow(request, username):
    current_user = request.fleek_user
    target_user = get_object_or_404(FUsers, username=username)
    if target_user != current_user:
        if target_user.followers.filter(id=current_user.id).exists():
            target_user.followers.remove(current_user)
        else:
            target_user.followers.add(current_user)
    return redirect("profile", username=username)


@auth_required
def edit_profile(request):
    current_user = request.fleek_user
    otp_key = f"profile_password_otp_{current_user.id}"
    otp_state = request.session.get(otp_key, {})
    otp_pending = bool(otp_state)

    if request.method == "POST":
        new_username = request.POST.get("username", "").strip() or current_user.username
        new_email = request.POST.get("email", "").strip() or current_user.email
        new_nickname = request.POST.get("nickname", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("password_confirm", "").strip()
        otp_code = request.POST.get("otp_code", "").strip()

        if new_username != current_user.username and FUsers.objects.filter(username=new_username).exists():
            messages.error(request, "That username is already taken.")
        elif new_email != current_user.email and FUsers.objects.filter(email=new_email).exists():
            messages.error(request, "That email is already registered.")
        else:
            current_user.username = new_username
            current_user.email = new_email
            current_user.nickname = new_nickname
            current_user.bio = request.POST.get("bio", "").strip()
            avatar_url = request.POST.get("avatar_url", "").strip()
            avatar_file = request.FILES.get("avatar_file")
            if avatar_file:
                if current_user.avatar_file:
                    current_user.avatar_file.delete(save=False)
                current_user.avatar_file = avatar_file
                current_user.avatar = ""
            elif avatar_url:
                if current_user.avatar_file:
                    current_user.avatar_file.delete(save=False)
                current_user.avatar = avatar_url
                current_user.avatar_file = None

            current_user.avatar_position_x = int(request.POST.get("avatar_position_x", current_user.avatar_position_x))
            current_user.avatar_position_y = int(request.POST.get("avatar_position_y", current_user.avatar_position_y))

            password_verified = False
            if password:
                if otp_code:
                    if not otp_state or otp_state.get("code") != otp_code:
                        messages.error(request, "Invalid OTP code. Please try again.")
                        otp_pending = True
                    elif timezone.now().timestamp() - otp_state.get("created_at", 0) > 900:
                        request.session.pop(otp_key, None)
                        messages.error(request, "OTP expired. Please request a new code.")
                        otp_pending = False
                    elif password != otp_state.get("new_password"):
                        messages.error(request, "Password does not match the one used to request OTP.")
                        otp_pending = True
                    else:
                        current_user.password = make_password(password)
                        request.session.pop(otp_key, None)
                        otp_pending = False
                        password_verified = True
                        messages.success(request, "Password updated successfully.")
                else:
                    if password != confirm_password:
                        messages.error(request, "Passwords do not match.")
                        otp_pending = False
                    else:
                        code = generate_otp()
                        request.session[otp_key] = {
                            "code": code,
                            "new_password": password,
                            "created_at": timezone.now().timestamp(),
                        }
                        try:
                            send_mail(
                                "Your Fleek password change OTP",
                                f"Your OTP for password change is: {code}",
                                "yourgmail@gmail.com",
                                [current_user.email],
                                fail_silently=True,
                            )
                            messages.info(request, "OTP sent to your email. Enter it below to confirm your password change.")
                        except Exception:
                            messages.error(request, "Unable to send OTP email. Try again later.")
                        otp_pending = True
                        current_user.save()
                        return render(
                            request,
                            "Fleek/edit_profile.html",
                            {
                                "current_user": current_user,
                                "otp_pending": otp_pending,
                            },
                        )

            if not password or password_verified:
                current_user.save()
                if not password:
                    messages.success(request, "Profile updated successfully.")
                return redirect("profile", username=current_user.username)

    return render(request, "Fleek/edit_profile.html", {"current_user": current_user, "otp_pending": otp_pending})


@auth_required
def toggle_like(request, post_id):
    current_user = request.fleek_user
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(post=post, user=current_user)
    if not created:
        like.delete()
    return redirect_back_to_post(request, post_id)


@auth_required
def add_comment(request, post_id):
    current_user = request.fleek_user
    post = get_object_or_404(Post, id=post_id)
    body = request.POST.get("body", "").strip()
    if body:
        Comment.objects.create(post=post, author=current_user, body=body)
    else:
        messages.error(request, "Comment cannot be empty.")
    return redirect_back_to_post(request, post_id)


@auth_required
def delete_comment(request, comment_id):
    current_user = request.fleek_user
    comment = get_object_or_404(Comment.objects.select_related("post", "author"), id=comment_id)
    if comment.author != current_user and comment.post.author != current_user:
        return redirect_back_to_post(request, comment.post_id)
    if request.method == "POST":
        post_id = comment.post_id
        next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"
        comment.delete()
        messages.success(request, "Comment deleted.")
        if "#" in next_url:
            next_url = next_url.split("#", 1)[0]
        return redirect(f"{next_url}#post-{post_id}")
    return redirect_back_to_post(request, comment.post_id)


@auth_required
def toggle_share(request, post_id):
    return redirect_back_to_post(request, post_id)


def logout_view(request):
    request.session.flush()
    return redirect("login")
