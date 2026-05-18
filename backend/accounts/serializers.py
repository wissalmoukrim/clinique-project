from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

from .models import User

class CustomTokenSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'role': self.user.role
        }

        return data 


class EmployeeUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    personnel_id = serializers.SerializerMethodField()
    telephone = serializers.SerializerMethodField()
    actif = serializers.SerializerMethodField()
    specialite = serializers.SerializerMethodField()
    experience = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "personnel_id",
            "role",
            "telephone",
            "is_active",
            "actif",
            "is_locked",
            "date_joined",
            "last_login",
            "specialite",
            "experience",
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.get_full_name().strip() or obj.username

    def get_personnel_id(self, obj):
        personnel = getattr(obj, "personnel", None)
        return personnel.id if personnel else None

    def get_telephone(self, obj):
        medecin = getattr(obj, "medecin", None)
        personnel = getattr(obj, "personnel", None)
        if medecin:
            return medecin.telephone
        if personnel:
            return personnel.telephone
        return ""

    def get_actif(self, obj):
        personnel = getattr(obj, "personnel", None)
        return obj.is_active and (personnel.actif if personnel else True)

    def get_specialite(self, obj):
        medecin = getattr(obj, "medecin", None)
        return medecin.specialite if medecin else ""

    def get_experience(self, obj):
        medecin = getattr(obj, "medecin", None)
        return medecin.experience if medecin else ""
