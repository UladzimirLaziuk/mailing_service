from typing import List

import requests
from django.conf import settings
from django.db.models import Q

from app import models
from mailing_service.celery import app
from celery.utils.log import get_task_logger


logger = get_task_logger(__name__)


DICT_MAP_FIELDS = {
    'code': 'code_phone',
    'tag': 'tag',

}


def write_result_status(pk, response):
    data_status =  True if response==200 else False
    models.MailingModel.objects.filter(id=pk).update(**{'status_message ': data_status})
    return

def send_request(pk, list_clients:List, message:str=None, **kwargs):
    path = 'https://probe.fbrq.cloud/v1/send/{pk}'
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MDE4Njg3MjksImlzcyI6ImZhYnJpcXVlIiwibmFtZSI6InVsYWR6aW1pcmJlbCJ9.NankvYM-GJkxeiHBBf5QOWKWRKZnarEQ1xxL2X_pwo4'
    token = settings.TOKEN_JWT
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'}


    for dict_client in  list_clients:
        data = {'id': dict_client.id, 'phone': dict_client.get('phone'), 'text': message}
        path = 'https://probe.fbrq.cloud/v1/send/{dict_client.id}'
        response = requests.post(path, json=data, headers=headers)
    return response.status_code


def get_queryset_clients_for_send(pk=None):
    """ Фильтрация Клиентов по тег или коду"""
    q = Q()
    q.connector = "OR"
    list_data = models.MailingModel.objects.filter(id=pk).get().filter_model.values()
    for element_table in list_data:
        key = element_table.get('name_filter')
        value = element_table.get('data_filter')
        query_name = DICT_MAP_FIELDS.get(key)
        if query_name:
            q.children.append((query_name, value))
    if q:
        return models.Client.objects.filter(q).distinct()
    return models.Client.objects.none()


@app.task(bind=True, name="send_message_to_client", max_retries=5)
def send_message_to_client(self, *args, to_email=None, pk=None, message=None, **kwargs):
    """Отправлене данных на сервер в случае ошибок 5 попыток повтора"""
    response = 100
    query_mailing = get_queryset_clients_for_send(pk)
    if query_mailing.exists():
        response = send_request(pk, query_mailing.values(), message)
        if response != 200:
            logger.info('retry')
            self.retry(countdown=2 ** self.request.retries)
    write_result_status(pk, response)
    return "Done"
