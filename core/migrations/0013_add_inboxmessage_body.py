from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_inboxmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='inboxmessage',
            name='body',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
    ]
