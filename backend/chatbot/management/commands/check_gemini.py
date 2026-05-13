from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from chatbot.services import call_gemini, gemini_error_summary


class Command(BaseCommand):
    help = "Check whether the configured Gemini API key and model can generate content."

    def handle(self, *args, **options):
        if not settings.GEMINI_API_KEY:
            raise CommandError("GEMINI_API_KEY is not configured.")

        self.stdout.write(f"Checking Gemini model: {settings.GEMINI_MODEL}")

        try:
            response = call_gemini("Reponds uniquement avec le mot: OK")
        except Exception as exc:
            raise CommandError(f"Gemini check failed: {gemini_error_summary(exc)}") from exc

        if not response:
            raise CommandError("Gemini check failed: empty response.")

        self.stdout.write(self.style.SUCCESS(f"Gemini check succeeded: {response[:120]}"))
