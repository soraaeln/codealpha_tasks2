from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_fix_profile_followers_join_table"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                PRAGMA foreign_keys=off;

                ALTER TABLE core_profile RENAME TO core_profile_old;
                CREATE TABLE core_profile (
                    id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    bio text NOT NULL,
                    avatar varchar(200) NOT NULL,
                    location varchar(120) NOT NULL,
                    website varchar(200) NOT NULL,
                    created_at datetime NOT NULL,
                    updated_at datetime NOT NULL,
                    user_id integer NOT NULL UNIQUE REFERENCES fusers (id) DEFERRABLE INITIALLY DEFERRED
                );
                INSERT INTO core_profile (id, bio, avatar, location, website, created_at, updated_at, user_id)
                SELECT id, bio, avatar, location, website, created_at, updated_at, user_id
                FROM core_profile_old;
                DROP TABLE core_profile_old;

                ALTER TABLE core_post RENAME TO core_post_old;
                CREATE TABLE core_post (
                    id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    caption text NOT NULL,
                    image_url varchar(200) NOT NULL,
                    created_at datetime NOT NULL,
                    author_id integer NOT NULL REFERENCES fusers (id) DEFERRABLE INITIALLY DEFERRED
                );
                INSERT INTO core_post (id, caption, image_url, created_at, author_id)
                SELECT id, caption, image_url, created_at, author_id
                FROM core_post_old;
                DROP TABLE core_post_old;

                PRAGMA foreign_keys=on;
            """,
            reverse_sql="""
                PRAGMA foreign_keys=off;

                ALTER TABLE core_profile RENAME TO core_profile_old;
                CREATE TABLE core_profile (
                    id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    bio text NOT NULL,
                    avatar varchar(200) NOT NULL,
                    location varchar(120) NOT NULL,
                    website varchar(200) NOT NULL,
                    created_at datetime NOT NULL,
                    updated_at datetime NOT NULL,
                    user_id integer NOT NULL UNIQUE REFERENCES auth_user (id) DEFERRABLE INITIALLY DEFERRED
                );
                INSERT INTO core_profile (id, bio, avatar, location, website, created_at, updated_at, user_id)
                SELECT id, bio, avatar, location, website, created_at, updated_at, user_id
                FROM core_profile_old;
                DROP TABLE core_profile_old;

                ALTER TABLE core_post RENAME TO core_post_old;
                CREATE TABLE core_post (
                    id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    caption text NOT NULL,
                    image_url varchar(200) NOT NULL,
                    created_at datetime NOT NULL,
                    author_id integer NOT NULL REFERENCES auth_user (id) DEFERRABLE INITIALLY DEFERRED
                );
                INSERT INTO core_post (id, caption, image_url, created_at, author_id)
                SELECT id, caption, image_url, created_at, author_id
                FROM core_post_old;
                DROP TABLE core_post_old;

                PRAGMA foreign_keys=on;
            """,
        ),
    ]
