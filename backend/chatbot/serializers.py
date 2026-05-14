from rest_framework import serializers


class ChatbotRequestSerializer(serializers.Serializer):
    message = serializers.CharField(allow_blank=True, max_length=500, trim_whitespace=True)


class ChatbotResponseSerializer(serializers.Serializer):
    response = serializers.CharField()
