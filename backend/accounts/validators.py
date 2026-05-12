import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class StrongPasswordValidator:
    def validate(self, password, user=None):
        if len(password or "") < 8:
            raise ValidationError(_("Password must contain at least 8 characters."), code="password_too_short")
        if not re.search(r"[a-z]", password):
            raise ValidationError(_("Password must contain a lowercase letter."), code="password_no_lower")
        if not re.search(r"[A-Z]", password):
            raise ValidationError(_("Password must contain an uppercase letter."), code="password_no_upper")
        if not re.search(r"\d", password):
            raise ValidationError(_("Password must contain a number."), code="password_no_number")
        if not re.search(r"[^A-Za-z0-9]", password):
            raise ValidationError(_("Password must contain a special character."), code="password_no_special")

    def get_help_text(self):
        return _("Use at least 8 characters with uppercase, lowercase, number and special character.")
