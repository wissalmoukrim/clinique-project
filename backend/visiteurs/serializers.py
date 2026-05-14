from rest_framework import serializers

from .models import JournalVisite, Visite, Visiteur


class VisiteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visiteur
        fields = ["id", "nom", "prenom", "cin", "telephone"]
        read_only_fields = fields


class JournalVisiteSerializer(serializers.ModelSerializer):
    visiteur_id = serializers.IntegerField(read_only=True)
    visiteur = serializers.StringRelatedField()
    agent_securite = serializers.SerializerMethodField()

    class Meta:
        model = JournalVisite
        fields = ["id", "visiteur_id", "visiteur", "agent_securite", "motif", "date_entree", "date_sortie", "statut"]
        read_only_fields = fields

    def get_agent_securite(self, obj):
        return obj.agent_securite.user.username if obj.agent_securite else None


class VisiteSerializer(serializers.ModelSerializer):
    visiteur_id = serializers.IntegerField(read_only=True)
    visiteur = serializers.StringRelatedField()

    class Meta:
        model = Visite
        fields = ["id", "visiteur_id", "visiteur", "motif", "date_entree", "date_sortie", "statut"]
        read_only_fields = fields
