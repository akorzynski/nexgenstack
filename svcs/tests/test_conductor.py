from rest_framework.test import APITestCase
from adrf.test import AsyncAPIClient
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User, Group
from svcs.models import (
    Flavor,
    ComputeNode,
    FloatingIP,
    Image,
    Environment,
    Key,
    VirtualMachine,
    VMKeyBinding,
    VMLabel,
)
from unittest.mock import patch, AsyncMock
import os
import aio_pika
import json


@patch.dict(os.environ, {"RABBITMQ_HOST": "your_rabbitmq_host"})
class VirtualMachineViewTests(APITestCase):
    def setUp(self):
        self.client = AsyncAPIClient()
        self.async_client = self.client
        self.user = User.objects.create_user(
            username="test_user", password="test_password"
        )
        self.token = Token.objects.create(user=self.user, key="test_token")

        self.group = Group.objects.create(name="TestGroup")
        self.user.groups.add(self.group)

        self.flavor = Flavor.objects.create(
            name="TestFlavor",
            cpu_cores=2,
            memory_mb=2048,
            disk_gb=20,
            gpu_type="TestGPU",
            gpu_count=1,
        )
        self.compute_node = ComputeNode.objects.create(
            name="compute-1",
            cpu_cores=2,
            memory_mb=2048,
            disk_gb=20,
            gpu_type="TestGPU",
            gpu_count=1,
        )
        ComputeNode.objects.create(
            name="compute-2",
            cpu_cores=2,
            memory_mb=2048,
            disk_gb=20,
            gpu_type="TestGPU",
            gpu_count=1,
        )
        self.floating_ip = FloatingIP.objects.create(
            ip_address="192.168.1.1",
        )
        FloatingIP.objects.create(
            ip_address="192.168.1.2",
        )
        self.image = Image.objects.create(
            name="TestImage",
        )
        self.environment = Environment.objects.create(name="TestEnv", group=self.group)
        self.key = Key.objects.create(
            name="TestKey",
            environment=self.environment,
            public_key="TestPublicKey",
        )
        self.virtual_machine = VirtualMachine.objects.create(
            name="TestVM",
            environment=self.environment,
            image=self.image,
            flavor=self.flavor,
            compute_node=self.compute_node,
            state="started",
        )
        self.vm_key_binding = VMKeyBinding.objects.create(
            virtual_machine=self.virtual_machine, key=self.key
        )
        self.vm_label = VMLabel.objects.create(
            virtual_machine=self.virtual_machine, name="TestLabel"
        )

    @patch("aio_pika.connect_robust", new_callable=AsyncMock)
    async def test_create_virtual_machine(self, mock_connect_robust):
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        mock_connect_robust.return_value.channel.return_value = mock_channel
        mock_channel.declare_exchange.return_value = mock_exchange
        url = reverse("virtual_machine")
        data = {
            "environment_name": self.environment.name,
            "image_name": self.image.name,
            "flavor_name": self.flavor.name,
            "key_names": [self.key.name],
            "assign_floating_ip": True,
            "name": "TestStandardVM",
            "labels": [ "TestStandardLabel" ],
        }
        response = await self.async_client.post(url, data, format="json", AUTHORIZATION=f"Token {self.token}")
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            msg=f"Response content: {response.content}",
        )
        mock_exchange.publish.assert_called_once()
        expected_message = {
            'id': 2,
            'name': "TestStandardVM",
            'state': 'started',
            'image': self.virtual_machine.image.name,
            'cpu_cores': self.virtual_machine.flavor.cpu_cores,
            'memory_mb': self.virtual_machine.flavor.memory_mb,
            'disk_gb': self.virtual_machine.flavor.disk_gb,
            'user_data': self.virtual_machine.user_data,
            'labels': [ "TestStandardLabel" ],
            'public_ip': self.floating_ip.ip_address,
        }
        published_message = mock_exchange.publish.call_args[0][0]
        self.assertEqual(json.loads(published_message.body), expected_message)
        self.assertEqual(published_message.delivery_mode, aio_pika.DeliveryMode.PERSISTENT)

    @patch("aio_pika.connect_robust", new_callable=AsyncMock)
    async def test_create_virtual_machine_without_floating_ip(
        self, mock_connect_robust
    ):
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        mock_connect_robust.return_value.channel.return_value = mock_channel
        mock_channel.declare_exchange.return_value = mock_exchange
        url = reverse("virtual_machine")
        data = {
            "environment_name": self.environment.name,
            "image_name": self.image.name,
            "flavor_name": self.flavor.name,
            "key_names": [self.key.name],
            "assign_floating_ip": False,
            "name": "TestVMWithoutIP",
        }
        response = await self.async_client.post(url, data, format="json", AUTHORIZATION=f"Token {self.token}")
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            msg=f"Response content: {response.content}",
        )
        mock_exchange.publish.assert_called_once()

    @patch("aio_pika.connect_robust", new_callable=AsyncMock)
    async def test_create_virtual_machine_with_missing_fields(
        self, mock_connect_robust
    ):
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        mock_connect_robust.return_value.channel.return_value = mock_channel
        mock_channel.declare_exchange.return_value = mock_exchange
        url = reverse("virtual_machine")
        data = {
            "environment_name": self.environment.name,
            "image_name": self.image.name,
            "assign_floating_ip": True,
            "name": "TestVMWithMissingFields",
        }
        response = await self.async_client.post(url, data, format="json", AUTHORIZATION=f"Token {self.token}")
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg=f"Response content: {response.content}",
        )
        mock_exchange.publish.assert_not_called()

    @patch("aio_pika.connect_robust", new_callable=AsyncMock)
    async def test_create_virtual_machine_with_invalid_data(self, mock_connect_robust):
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        mock_connect_robust.return_value.channel.return_value = mock_channel
        mock_channel.declare_exchange.return_value = mock_exchange
        url = reverse("virtual_machine")
        data = {
            "environment_name": self.environment.name,
            "image_name": self.image.name,
            "flavor_name": self.flavor.name,
            "key_names": [self.key.name],
            "assign_floating_ip": True,
            "name": "",
        }
        response = await self.async_client.post(url, data, format="json", AUTHORIZATION=f"Token {self.token}")
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg=f"Response content: {response.content}",
        )
        mock_exchange.publish.assert_not_called()

    @patch("aio_pika.connect_robust", new_callable=AsyncMock)
    async def test_delete_virtual_machine_by_id(self, mock_connect_robust):
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        mock_connect_robust.return_value.channel.return_value = mock_channel
        mock_channel.declare_exchange.return_value = mock_exchange
        url = reverse("virtual_machine_by_id", args=[self.virtual_machine.id])
        response = await self.async_client.delete(url, AUTHORIZATION=f"Token {self.token}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(
            (await VirtualMachine.objects.aget(pk=self.virtual_machine.id)).state,
            "deleting",
        )
        mock_exchange.publish.assert_called_once()

    @patch("aio_pika.connect_robust", new_callable=AsyncMock)
    async def test_patch_virtual_machine_state(self, mock_connect_robust):
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        mock_connect_robust.return_value.channel.return_value = mock_channel
        mock_channel.declare_exchange.return_value = mock_exchange
        url = reverse("virtual_machine_update_state", args=[self.virtual_machine.id])
        data = {"state": "started"}
        response = await self.async_client.patch(url, data, format="json", AUTHORIZATION=f"Token {self.token}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["state"], "started")
        await self.virtual_machine.arefresh_from_db()
        self.assertEqual(self.virtual_machine.state, "started")
        mock_exchange.publish.assert_not_called()

    @patch("aio_pika.connect_robust", new_callable=AsyncMock)
    async def test_patch_virtual_machine_state_missing(self, mock_connect_robust):
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        mock_connect_robust.return_value.channel.return_value = mock_channel
        mock_channel.declare_exchange.return_value = mock_exchange
        url = reverse("virtual_machine_update_state", args=[self.virtual_machine.id])
        data = {}
        response = await self.async_client.patch(url, data, format="json", AUTHORIZATION=f"Token {self.token}")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "state is required")
        mock_exchange.publish.assert_not_called()
