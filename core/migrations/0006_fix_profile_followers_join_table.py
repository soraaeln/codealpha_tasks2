from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_restore_fusers_schema"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                DROP TABLE IF EXISTS core_profile_followers;
                CREATE TABLE core_profile_followers (
                    id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    profile_id bigint NOT NULL REFERENCES core_profile (id) DEFERRABLE INITIALLY DEFERRED,
                    fusers_id bigint NOT NULL REFERENCES fusers (id) DEFERRABLE INITIALLY DEFERRED
                );
            """,
            reverse_sql="""
                DROP TABLE IF EXISTS core_profile_followers;
            """,
        ),
    ]
