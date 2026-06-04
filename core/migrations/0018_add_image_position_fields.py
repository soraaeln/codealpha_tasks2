from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0017_merge_nickname_and_video"),
    ]

    operations = [
        migrations.AddField(
            model_name="fusers",
            name="avatar_position_x",
            field=models.PositiveSmallIntegerField(default=50),
        ),
        migrations.AddField(
            model_name="fusers",
            name="avatar_position_y",
            field=models.PositiveSmallIntegerField(default=50),
        ),
        migrations.AddField(
            model_name="post",
            name="media_position_x",
            field=models.PositiveSmallIntegerField(default=50),
        ),
        migrations.AddField(
            model_name="post",
            name="media_position_y",
            field=models.PositiveSmallIntegerField(default=50),
        ),
    ]
