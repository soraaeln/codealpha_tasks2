from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_post_profile_delete_fusers_delete_pendingsignup"),
    ]

    operations = [
        migrations.CreateModel(
            name="FUsers",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("username", models.CharField(max_length=100, unique=True)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("password", models.CharField(max_length=255)),
                ("is_verified", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "fusers"},
        ),
        migrations.CreateModel(
            name="PendingSignup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("username", models.CharField(max_length=100)),
                ("email", models.EmailField(max_length=254)),
                ("password_hash", models.CharField(max_length=255)),
                ("code", models.CharField(max_length=6)),
                ("is_used", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AlterField(
            model_name="post",
            name="author",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="posts", to="core.fusers"),
        ),
        migrations.AlterField(
            model_name="profile",
            name="user",
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to="core.fusers"),
        ),
        migrations.AlterField(
            model_name="profile",
            name="followers",
            field=models.ManyToManyField(blank=True, related_name="following_profiles", to="core.fusers"),
        ),
    ]
