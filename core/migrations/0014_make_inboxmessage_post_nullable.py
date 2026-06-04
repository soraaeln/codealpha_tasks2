from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_add_inboxmessage_body'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inboxmessage',
            name='post',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='inbox_messages',
                to='core.post',
            ),
        ),
    ]
