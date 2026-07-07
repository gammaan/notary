import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from operations.models import ServiceType


class Command(BaseCommand):
    help = "Seed default service types from data/services.json"

    def handle(self, *args, **options):
        path = Path(settings.BASE_DIR) / "data" / "services.json"
        if not path.exists():
            self.stderr.write(self.style.ERROR(f"File not found: {path}"))
            return

        data = json.loads(path.read_text(encoding="utf-8"))
        items = data.get("items", [])
        created = 0
        updated = 0

        for index, item in enumerate(items):
            name = item.get("title", "").strip()
            if not name:
                continue
            description = item.get("copy", "").strip()
            obj, was_created = ServiceType.objects.update_or_create(
                name=name,
                defaults={
                    "description": description,
                    "sort_order": index,
                    "is_active": True,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Service types ready: {created} created, {updated} updated."
            )
        )
