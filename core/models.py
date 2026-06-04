from django.db import models


class FUsers(models.Model):
    username = models.CharField(max_length=100, unique=True)
    nickname = models.CharField(max_length=100, blank=True, default="")
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    is_verified = models.BooleanField(default=False)
    bio = models.TextField(blank=True)
    avatar = models.URLField(blank=True)
    location = models.CharField(max_length=120, blank=True)
    website = models.URLField(blank=True)
    avatar_file = models.FileField(upload_to="avatars/", blank=True, null=True)
    avatar_position_x = models.PositiveSmallIntegerField(default=50)
    avatar_position_y = models.PositiveSmallIntegerField(default=50)
    followers = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="following",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def avatar_url(self):
        if self.avatar_file:
            return self.avatar_file.url
        return self.avatar

    def __str__(self):
        return self.username

    class Meta:
        db_table = "fusers"


class PendingSignup(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField()
    password_hash = models.CharField(max_length=255)
    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class Post(models.Model):
    author = models.ForeignKey(
        FUsers,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    caption = models.TextField()
    image_url = models.URLField(blank=True)
    image_file = models.FileField(upload_to="posts/", blank=True, null=True)
    video_file = models.FileField(upload_to="posts/", blank=True, null=True)
    media_position_x = models.PositiveSmallIntegerField(default=50)
    media_position_y = models.PositiveSmallIntegerField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def media_src(self):
        if self.video_file:
            return self.video_file.url
        if self.image_file:
            return self.image_file.url
        return self.image_url

    @property
    def is_video(self):
        return bool(self.video_file)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author.username}: {self.caption[:30]}"


class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(FUsers, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["post", "user"], name="unique_post_like")
        ]

    def __str__(self):
        return f"{self.user.username} likes {self.post_id}"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(FUsers, on_delete=models.CASCADE, related_name="comments")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author.username} on {self.post_id}"


class Share(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="shares")
    user = models.ForeignKey(FUsers, on_delete=models.CASCADE, related_name="shares")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["post", "user"], name="unique_post_share")
        ]

    def __str__(self):
        return f"{self.user.username} shared {self.post_id}"


class PostShare(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_shares")
    sender = models.ForeignKey(FUsers, on_delete=models.CASCADE, related_name="sent_post_shares")
    recipient = models.ForeignKey(FUsers, on_delete=models.CASCADE, related_name="received_post_shares")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "sender", "recipient"],
                name="unique_post_share_recipient",
            )
        ]

    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username}: {self.post_id}"


class InboxMessage(models.Model):
    sender = models.ForeignKey(FUsers, on_delete=models.CASCADE, related_name="sent_messages")
    recipient = models.ForeignKey(FUsers, on_delete=models.CASCADE, related_name="received_messages")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="inbox_messages", null=True, blank=True)
    body = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        if self.post_id:
            return f"{self.sender.username} -> {self.recipient.username}: post {self.post_id}"
        return f"{self.sender.username} -> {self.recipient.username}: {self.body[:30]}"
