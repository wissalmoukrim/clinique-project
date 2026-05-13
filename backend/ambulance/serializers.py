from rest_framework import serializers

from .models import Ambulance, MissionAmbulance


class AmbulanceSerializer(serializers.ModelSerializer):
    chauffeur = serializers.SerializerMethodField()
    chauffeur_display = serializers.SerializerMethodField()

    class Meta:
        model = Ambulance
        fields = ["id", "matricule", "type", "disponible", "chauffeur", "chauffeur_display"]
        read_only_fields = fields

    def get_chauffeur(self, obj):
        return obj.chauffeur.user.username if obj.chauffeur else None

    def get_chauffeur_display(self, obj):
        if not obj.chauffeur:
            return None
        return obj.chauffeur.user.get_full_name().strip() or obj.chauffeur.user.username


class MissionAmbulanceSerializer(serializers.ModelSerializer):
    ambulance_id = serializers.IntegerField(read_only=True)
    ambulance = serializers.CharField(source="ambulance.matricule", read_only=True)
    chauffeur = serializers.SerializerMethodField()
    chauffeur_display = serializers.SerializerMethodField()

    class Meta:
        model = MissionAmbulance
        fields = [
            "id",
            "ambulance_id",
            "ambulance",
            "chauffeur",
            "chauffeur_display",
            "patient_nom",
            "lieu_depart",
            "lieu_arrivee",
            "date",
            "statut",
        ]
        read_only_fields = fields

    def get_chauffeur(self, obj):
        return obj.chauffeur.user.username if obj.chauffeur else None

    def get_chauffeur_display(self, obj):
        if not obj.chauffeur:
            return None
        return obj.chauffeur.user.get_full_name().strip() or obj.chauffeur.user.username
