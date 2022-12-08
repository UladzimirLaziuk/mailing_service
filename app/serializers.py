from rest_framework import serializers

from app.models import Client, MailingModel, FilterMailingModel
from app.signals import new_signal


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'


class FilterMailingSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilterMailingModel
        exclude = ('mailing_model',)


class MailingModelSerializer(serializers.ModelSerializer):
    filter_models = FilterMailingSerializer(write_only=True, many=True)
    filter_model = FilterMailingSerializer(read_only=True, many=True)

    class Meta:
        model = MailingModel
        fields = ('data_start_work', 'data_end_work', 'message', 'filter_models', 'filter_model')

    def create(self, validated_data):
        filter_models = validated_data.pop('filter_models')
        instance = super().create(validated_data)
        for dt in filter_models:
            FilterMailingModel.objects.create(**dt, mailing_model=instance)
        new_signal.send(sender=MailingModelSerializer, instance=instance)
        return instance
