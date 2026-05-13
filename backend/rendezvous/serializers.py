from rest_framework import serializers

from .models import RendezVous


class RendezVousSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField(read_only=True)
    patient = serializers.CharField(source="patient.user.username", read_only=True)
    patient_full_name = serializers.SerializerMethodField()
    patient_display = serializers.SerializerMethodField()
    medecin_id = serializers.IntegerField(read_only=True)
    medecin = serializers.CharField(source="medecin.user.username", read_only=True)
    medecin_full_name = serializers.SerializerMethodField()
    medecin_display = serializers.SerializerMethodField()
    specialite = serializers.CharField(source="medecin.specialite", read_only=True)

    class Meta:
        model = RendezVous
        fields = [
            "id",
            "patient_id",
            "patient",
            "patient_full_name",
            "patient_display",
            "medecin_id",
            "medecin",
            "medecin_full_name",
            "medecin_display",
            "specialite",
            "date",
            "heure",
            "statut",
        ]
        read_only_fields = fields

    def get_patient_full_name(self, obj):
        return obj.patient.user.get_full_name().strip() or obj.patient.user.username

    def get_patient_display(self, obj):
        return self.get_patient_full_name(obj)

    def get_medecin_full_name(self, obj):
        return obj.medecin.user.get_full_name().strip() or obj.medecin.user.username

    def get_medecin_display(self, obj):
        return f"Dr. {self.get_medecin_full_name(obj)}"
