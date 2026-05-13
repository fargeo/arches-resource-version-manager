import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("models", "12586_tile_cardinality_check"),
    ]

    operations = [
        migrations.CreateModel(
            name="ResourceVersion",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("resource_group_id", models.CharField(max_length=255)),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("draft", "draft"),
                            ("final", "final"),
                            ("archived", "archived"),
                        ],
                        default="draft",
                        max_length=50,
                    ),
                ),
                ("version", models.CharField(blank=True, max_length=255, null=True)),
                ("payload", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("editable", models.BooleanField(default=False)),
                (
                    "resourceinstanceid",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="models.resourceinstance",
                    ),
                ),
            ],
            options={
                "db_table": "resource_version",
                "managed": True,
            },
        ),
    ]
