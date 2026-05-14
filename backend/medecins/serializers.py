from rest_framework import serializers

from .models import Medecin


class MedecinSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    full_name = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Medecin
        fields = [
            "id",
            "user_id",
            "username",
            "full_name",
            "display_name",
            "specialite",
            "telephone",
            "numero_ordre",
            "disponible",
            "experience",
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.user.get_full_name().strip() or obj.user.username

    def get_display_name(self, obj):
        return f"Dr. {self.get_full_name(obj)}"
