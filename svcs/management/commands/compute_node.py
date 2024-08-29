import os
import pika
from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import json
from django.urls import reverse
from .sdk import Client

class Command(BaseCommand):
    help = 'Compute node service: listen to RabbitMQ queue'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.compute_node_name = os.getenv('COMPUTE_NODE_NAME')
        if not self.compute_node_name:
            raise ValueError('COMPUTE_NODE_NAME environment variable is not set')

        self.compute_node_token = os.getenv('COMPUTE_NODE_TOKEN')
        if not self.compute_node_token:
            raise ValueError('COMPUTE_NODE_TOKEN environment variable is not set')

        self.conductor_api_url = os.getenv('CONDUCTOR_API_URL')
        if not self.conductor_api_url:
            raise ValueError('CONDUCTOR_API_URL environment variable is not set')

        self.rabbitmq_host = os.getenv('RABBITMQ_HOST')
        if not self.rabbitmq_host:
            raise ValueError('RABBITMQ_HOST environment variable is not set')

        self.rabbitmq_port = os.getenv('RABBITMQ_PORT')
        if not self.rabbitmq_port:
            self.rabbitmq_port = 5672

        hypervisor_client_api_key = os.getenv('HYPERVISOR_CLIENT_API_KEY')
        if not hypervisor_client_api_key:
            raise ValueError('HYPERVISOR_CLIENT_API_KEY environment variable is not set')
        self.client = Client(api_key=hypervisor_client_api_key)
        self.client.authenticate()

    def virtual_machine_update_state(self, vm_id, hypervisor_id, state):
        relative_url = reverse('virtual_machine_update_state', kwargs={'pk': vm_id})
        url = f"{self.conductor_api_url}{relative_url}"
        payload = {
            'id': vm_id,
            'hypervisor_id': hypervisor_id,
            'state': state
        }
        headers = {'Content-Type': 'application/json'}
        headers['Authorization'] = f'Token {self.compute_node_token}'
        response = requests.patch(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f'Failed to notify conductor about state change for VM {vm_id}')
        self.stdout.write(self.style.SUCCESS(f'Successfully notified conductor about state change for VM {vm_id}'))

    def virtual_machine_delete(self, vm_id):
        relative_url = reverse('virtual_machine_by_id', kwargs={'pk': vm_id})
        url = f"{self.conductor_api_url}{relative_url}"
        headers = { }
        headers['Authorization'] = f'Token {self.compute_node_token}'
        response = requests.delete(url, headers=headers)
        if response.status_code != 204:
            raise Exception(f'Failed to notify conductor about VM deletion for VM {vm_id}')
        self.stdout.write(self.style.SUCCESS(f'Successfully notified conductor about VM deletion for VM {vm_id}'))

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f'Starting RabbitMQ listener on compute node {self.compute_node_name}...'))

        connection_params = pika.ConnectionParameters(host=self.rabbitmq_host, port=self.rabbitmq_port)
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        channel.exchange_declare(exchange=settings.EXCHANGE_NAME, exchange_type='direct', durable=True)
        queue_name = f"q.{self.compute_node_name}"
        channel.queue_declare(queue=queue_name, durable=True)
        channel.queue_bind(exchange=settings.EXCHANGE_NAME, queue=queue_name, routing_key=queue_name)

        def callback(ch, method, properties, body):
            vm_id = None
            hypervisor_id = None
            try:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{self.compute_node_name}: received {body} with routing key {method.routing_key}"
                    )
                )
                message = json.loads(body.decode('utf-8'))
                vm_id = message["id"]
                requested_state = message["state"]
                if requested_state == 'started':
                    vm = self.client.create_vm(
                        name=message["name"],
                        cpu_cores=message["cpu_cores"],
                        memory=message["memory_mb"],
                        disk_size=message["disk_gb"],
                        public_ip=message["public_ip"],
                        labels=message["labels"],
                    )
                    hypervisor_id = vm.id
                    self.virtual_machine_update_state(vm_id, hypervisor_id, requested_state)
                elif requested_state == 'deleted':
                    hypervisor_id = message['hypervisor_id']
                    self.client.delete_vm(hypervisor_id)
                    self.virtual_machine_delete(vm_id)
                else:
                    raise Exception(f"Invalid state {requested_state} for VM {vm_id}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except BaseException as e:
                self.stdout.write(self.style.ERROR(f"Error processing message: {e}"))
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                if vm_id is not None:
                    self.virtual_machine_update_state(vm_id, hypervisor_id, "failed")

        channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback,
            auto_ack=False,
        )
        self.stdout.write(self.style.SUCCESS('Waiting for messages. To exit press CTRL+C'))
        channel.start_consuming()
