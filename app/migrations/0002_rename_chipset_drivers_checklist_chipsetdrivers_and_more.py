# Generated by Django 5.2.1 on 2025-06-05 07:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="checklist",
            old_name="chipset_drivers",
            new_name="chipsetDrivers",
        ),
        migrations.RenameField(
            model_name="checklist",
            old_name="graphics_drivers",
            new_name="graphicsDrivers",
        ),
        migrations.RemoveField(
            model_name="checklist",
            name="testing",
        ),
    ]
