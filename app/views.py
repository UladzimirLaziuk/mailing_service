from app.models import Client, MailingModel
from app.serializers import ClientSerializer, MailingModelSerializer
from rest_framework import viewsets


# Create your views here.
class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer


class MailingModelViewSet(viewsets.ModelViewSet):
    queryset = MailingModel.objects.all()
    serializer_class = MailingModelSerializer
