from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_inboxmessage"),
    ]

    operations = [
        migrations.AddField(
            model_name="fusers",
            name="nickname",
            field=models.CharField(blank=True, max_length=100, default=""),
        ),
    ]
