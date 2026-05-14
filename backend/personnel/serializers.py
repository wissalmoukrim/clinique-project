from rest_framework import serializers

from .models import Personnel


class PersonnelSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    role = serializers.CharField(source="user.role", read_only=True)

    class Meta:
        model = Personnel
        fields = ["id", "user_id", "username", "role", "fonction", "telephone", "adresse", "actif"]
        read_only_fields = fields
