from mailing_service.tasks import send_message_to_client
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


from django.dispatch import receiver
import logging

from app.signals import new_signal

logger = logging.getLogger('root')


class MailingModel(models.Model):
    """
    Сущность "рассылка" имеет атрибуты:
    •уникальный id рассылки
    •дата и время запуска рассылки
    •текст сообщения для доставки клиенту
    •фильтр свойств клиентов, на которых должна быть произведена рассылка (код мобильного оператора, тег)
    •дата и время окончания рассылки: если по каким-то причинам не успели разослать все сообщения -
    никакие сообщения клиентам после этого времени доставляться не должны
    """
    data_start_work = models.DateTimeField()
    message = models.CharField(max_length=255)
    data_end_work = models.DateTimeField()


class FilterMailingModel(models.Model):
    name_filter = models.CharField(max_length=50)
    data_filter = models.CharField(max_length=50)
    mailing_model = models.ForeignKey(MailingModel, on_delete=models.CASCADE, related_name='filter_model')


class Client(models.Model):
    """
    Сущность "клиент" имеет атрибуты:
        •уникальный id клиента
        •номер телефона клиента в формате 7XXXXXXXXXX (X - цифра от 0 до 9)
        •код мобильного оператора
        •тег (произвольная метка)
        •часовой пояс
    """
    # r = regex=r'^\+?1?\d{9,15}$'

    phone_regex = RegexValidator(regex=r'^7[0-9]{10}',
                                 message="номер телефона клиента в формате 7XXXXXXXXXX (X - цифра от 0 до 9)")
    phone = models.CharField(validators=[phone_regex], max_length=60)
    code_phone = models.CharField(max_length=50)
    tag = models.CharField(max_length=50)
    time_zone = models.CharField(max_length=50)


class MessageModel(models.Model):
    """
        Сущность "сообщение" имеет атрибуты:
            •уникальный id сообщения
            •дата и время создания (отправки)
            •статус отправки
            •id рассылки, в рамках которой было отправлено сообщение
            •id клиента, которому отправили
    """
    data_create = models.DateTimeField(auto_created=True)
    status_message = models.CharField(max_length=250)
    mailing_model = models.ForeignKey(MailingModel, on_delete=models.CASCADE)
    mailing_client = models.ForeignKey(Client, on_delete=models.CASCADE)




@receiver(new_signal)
def get_send_email(instance, **kwargs):
    pk = instance.pk
    data_start_work = instance.data_start_work
    data_end_work = instance.data_end_work
    logger.info(
        f'Create model Mailing and FilterMailingModel- {pk} '
        f' start-{data_start_work}'
        f' end-{data_end_work}')
    now = timezone.now()

    if data_start_work < now <= data_end_work:
        logger.info(f'send mailing func - {instance.id}  start-{instance.data_start_work} end-{instance.data_end_work}')
        send_message_to_client.delay(data_start_work=data_start_work, data_end_work=data_end_work, pk=pk)
    elif now < data_start_work:
        kwargs = {'pk':pk}
        kwargs.update({'message':instance.message})
        send_message_to_client.apply_async(eta=data_start_work, retry=True, kwargs=kwargs)
