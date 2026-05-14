from rest_framework import serializers

from .models import Chambre, Hospitalisation


class ChambreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chambre
        fields = ["id", "numero", "type", "disponible"]
        read_only_fields = fields


class HospitalisationSerializer(serializers.ModelSerializer):
    patient = serializers.CharField(source="patient.user.username", read_only=True)
    patient_id = serializers.IntegerField(read_only=True)
    patient_full_name = serializers.SerializerMethodField()
    patient_display = serializers.SerializerMethodField()
    chambre = serializers.SerializerMethodField()

    class Meta:
        model = Hospitalisation
        fields = [
            "id",
            "patient",
            "patient_id",
            "patient_full_name",
            "patient_display",
            "chambre",
            "date_entree",
            "date_sortie",
            "statut",
            "motif",
            "observations",
            "temperature",
            "tension",
            "frequence_cardiaque",
        ]
        read_only_fields = fields

    def get_patient_full_name(self, obj):
        return obj.patient.user.get_full_name().strip() or obj.patient.user.username

    def get_patient_display(self, obj):
        return self.get_patient_full_name(obj)

    def get_chambre(self, obj):
        return obj.chambre.numero if obj.chambre else None
