import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from accounts.models import User


VALID_ROLES = {choice[0] for choice in User.ROLE_CHOICES}
DEFAULT_PASSWORD = "1234"


def main():
    users = User.objects.all().order_by("username")

    if not users.exists():
        print("Aucun utilisateur trouve.")
        return

    for user in users:
        role_status = "OK" if user.role in VALID_ROLES else "ROLE INVALIDE"

        user.set_password(DEFAULT_PASSWORD)
        user.is_locked = False
        user.login_attempts = 0
        user.last_failed_login = None
        user.save(update_fields=[
            "password",
            "is_locked",
            "login_attempts",
            "last_failed_login",
        ])

        print(f"{user.username} | role={user.role} | {role_status} | password reset")

    print(f"\nTermine. Tous les utilisateurs peuvent se connecter avec password={DEFAULT_PASSWORD}")


if __name__ == "__main__":
    main()
