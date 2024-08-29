from adrf.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import aget_object_or_404
from django.conf import settings
from django.db.models import Subquery
from .models import VirtualMachine, Environment, ComputeNode, FloatingIP
from .serializers import VirtualMachineSerializer
import aio_pika
import json
import os

class VirtualMachineView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    async def post(self, request, *args, **kwargs):
        serializer = VirtualMachineSerializer(data=request.data, context={'user': request.user})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        vm, public_ip = await serializer.asave()
        await self.request_vm_start(vm, serializer.validated_data.get('labels'), public_ip)
        return Response({
            'id': vm.id,
            'name': vm.name,
            'environment_name': vm.environment.name,
            'state': vm.state,
            'public_ip': public_ip,
        }, status=status.HTTP_201_CREATED)

    async def delete(self, request, pk):
        vm = await aget_object_or_404(VirtualMachine, pk=pk)
        compute_node = await aget_object_or_404(ComputeNode, pk=vm.compute_node_id)
        if vm.state in [ 'deleting', 'failed' ]:
            await vm.adelete()
        else:
            vm.state = 'deleting'
            await vm.asave()
            await self.request_vm_delete(compute_node.name, vm.id, vm.hypervisor_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    async def patch(self, request, pk):
        vm = await aget_object_or_404(VirtualMachine, pk=pk)
        environment = await aget_object_or_404(Environment, pk=vm.environment_id)

        vm_hypervisor_id = request.data.get('hypervisor_id')
        if vm_hypervisor_id is not None:
            vm.hypervisor_id = vm_hypervisor_id

        state = request.data.get('state')
        if state is None:
            return Response({
                'error': 'state is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        vm.state = state

        await vm.asave()
        if vm.state == 'failed':
            assigned_floating_ip = (
                FloatingIP.objects.filter(virtual_machine=vm).values('id')
            )
            await FloatingIP.objects.filter(
                id=Subquery(assigned_floating_ip)
            ).aupdate(virtual_machine=None)

        return Response({
            'id': vm.id,
            'name': vm.name,
            'environment_name': environment.name,
            'state': vm.state
        }, status=status.HTTP_200_OK)

    rabbitmq_channel = None
    rabbitmq_exchange = None

    async def init_rabbitmq(self):
        if self.rabbitmq_channel is not None and not self.rabbitmq_channel.is_closed:
            return
        rabbitmq_host = os.environ.get("RABBITMQ_HOST")
        if not rabbitmq_host:
            raise ValueError("RABBITMQ_HOST environment variable is not set")
        rabbitmq_port = os.environ.get("RABBITMQ_PORT")
        if not rabbitmq_port:
            rabbitmq_port = 5672
        else:
            rabbitmq_port = int(rabbitmq_port)
        connection = await aio_pika.connect_robust(host=rabbitmq_host, port=rabbitmq_port)
        self.rabbitmq_channel = await connection.channel()
        self.rabbitmq_exchange = await self.rabbitmq_channel.declare_exchange(
            settings.EXCHANGE_NAME, aio_pika.ExchangeType.DIRECT, durable=True
        )

    async def request_vm_start(self, vm, labels, public_ip=None):
        await self.init_rabbitmq()
        queue_name = f"q.{vm.compute_node.name}"
        queue = await self.rabbitmq_channel.declare_queue(queue_name, durable=True)
        await queue.bind(self.rabbitmq_exchange, routing_key=queue_name)
        message = {
            'id': vm.id,
            'name': vm.name,
            'state': 'started',
            'image': vm.image.name,
            'cpu_cores': vm.flavor.cpu_cores,
            'memory_mb': vm.flavor.memory_mb,
            'disk_gb': vm.flavor.disk_gb,
            'user_data': vm.user_data,
            'labels': labels,
            'public_ip': public_ip,
        }
        await self.rabbitmq_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=queue_name,
        )

    async def request_vm_delete(self, compute_node_name, vm_id, vm_hypervisor_id):
        await self.init_rabbitmq()
        queue_name = f"q.{compute_node_name}"
        queue = await self.rabbitmq_channel.declare_queue(queue_name, durable=True)
        await queue.bind(self.rabbitmq_exchange, routing_key=queue_name)
        message = {
            'id': vm_id,
            'hypervisor_id': vm_hypervisor_id,
            'state': 'deleted',
        }
        await self.rabbitmq_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=queue_name,
        )
