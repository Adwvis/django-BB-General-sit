from django.core.management.base import BaseCommand
from accounts.models import User, Team


class Command(BaseCommand):
    help = "Create test16..test30 users assigned to ThpIssunigAgent team"

    def handle(self, *args, **options):
        try:
            team = Team.objects.get(name="ThpIssunigAgent")
        except Team.DoesNotExist:
            self.stderr.write(self.style.ERROR("Team 'ThpIssunigAgent' not found"))
            return

        for i in range(16, 31):
            username = f"test{i}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"is_active": True, "team": team},
            )
            if created:
                user.set_password("Test@123456")
                user.save()
                self.stdout.write(self.style.SUCCESS(f"created {username}"))
            else:
                user.team = team
                user.save(update_fields=["team"])
                self.stdout.write(f"{username} already existed, team updated")

        self.stdout.write(self.style.SUCCESS("Done."))