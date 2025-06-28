# attendance/management/commands/create_users_from_csv.py
import csv, secrets, sys
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from attendance.models import Student     # adjust if you have Lecturer model

User = get_user_model()

class Command(BaseCommand):
    """
    Usage:
      python manage.py create_users_from_csv students.csv --role student
      python manage.py create_users_from_csv lecturers.csv --role lecturer
    CSV columns (header row required):
      matric_id,name,email
    """
    help = "Bulk-create users from a CSV and e-mail credentials"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to CSV file")
        parser.add_argument("--role", choices=["student", "lecturer"], default="student")

    def handle(self, *args, **opts):
        csv_path = Path(opts["csv_path"])
        role     = opts["role"]
        if not csv_path.exists():
            raise CommandError(f"{csv_path} not found")

        with csv_path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            created, skipped = 0, 0

            for row in reader:
                username = row["matric_id"].strip().lower()
                email    = row["email"].strip().lower()
                full     = row["name"].strip()

                if User.objects.filter(username=username).exists():
                    self.stdout.write(self.style.WARNING(f"Skip existing {username}"))
                    skipped += 1
                    continue

                # ---- create user ----
                password = secrets.token_urlsafe(8)  # 12-char psw
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=email,
                    first_name=full.split()[0],
                    last_name=" ".join(full.split()[1:]),
                    is_staff = role=="lecturer"
                )

                # ---- link Student row (for facial encoding) ----
                if role == "student":
                    Student.objects.create(user=user)

                # ---- e-mail credentials ----
                subject = "Your initial FYP Attendance login"
                body = (f"Hi {full},\n\n"
                        f"Username (Matric): {username}\n"
                        f"Temporary password: {password}\n\n"
                        "Please log in and change your password immediately.\n"
                        "URL: https://attendance.youruni.edu/login/\n\n"
                        "Regards,\nAttendance System")
                try:
                    send_mail(subject, body, None, [email], fail_silently=False)
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Email fail for {username}: {e}"))

                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created: {created}, Skipped: {skipped}"
        ))
