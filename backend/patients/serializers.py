from rest_framework import serializers

from .models import Patient


class PatientSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    full_name = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = [
            "id",
            "user_id",
            "username",
            "email",
            "full_name",
            "display_name",
            "telephone",
            "adresse",
            "date_naissance",
            "sexe",
            "groupe_sanguin",
            "allergies",
            "antecedents",
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.user.get_full_name().strip() or obj.user.username

    def get_display_name(self, obj):
        return self.get_full_name(obj)
