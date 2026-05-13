from rest_framework import serializers

from .models import Facture, Paiement


class FactureSerializer(serializers.ModelSerializer):
    patient = serializers.CharField(source="patient.user.username", read_only=True)
    patient_id = serializers.IntegerField(read_only=True)
    patient_full_name = serializers.SerializerMethodField()
    patient_display = serializers.SerializerMethodField()
    montant = serializers.SerializerMethodField()

    class Meta:
        model = Facture
        fields = ["id", "patient", "patient_id", "patient_full_name", "patient_display", "montant", "date", "statut"]
        read_only_fields = fields

    def get_patient_full_name(self, obj):
        return obj.patient.user.get_full_name().strip() or obj.patient.user.username

    def get_patient_display(self, obj):
        return self.get_patient_full_name(obj)

    def get_montant(self, obj):
        return float(obj.montant)


class PaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paiement
        fields = ["id", "facture", "montant", "date", "mode"]
        read_only_fields = fields
