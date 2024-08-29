import pytest
import unittest

from unittest.mock import patch

from svcs.management.commands.sdk import Client
from svcs.management.commands.sdk.exceptions import AuthenticationError, NoResourcesAvailableError
from svcs.management.commands.sdk.models import VirtualMachine

class HypervisorClientTests(unittest.TestCase):

    def test_authenticate(self):
        client = Client(api_key="1234")
        client.authenticate()
        assert client.authenticated is True


    def test_authenticate__without_api_key(self):
        client = Client(api_key=None)
        with pytest.raises(AuthenticationError):
            client.authenticate()


    @patch("svcs.management.commands.sdk.client.uuid4", return_value="uuid4")
    @patch("svcs.management.commands.sdk.client.random.randint", return_value=0)
    def test_create_vm(self, mock_randint, mock_uuid4):
        client = Client(api_key="1234")
        client.authenticate()
        vm = client.create_vm(name="my-vm", cpu_cores=1, memory=512, disk_size=10)

        assert vm == VirtualMachine(
            id="uuid4",
            name="my-vm",
            cpu_cores=1,
            memory=512,
            disk_size=10,
        )


    @patch("svcs.management.commands.sdk.client.random.randint", return_value=1)
    def test_create_vm__fails_with_no_resources_available(self, mock_randint):
        client = Client(api_key="1234")
        client.authenticate()

        with pytest.raises(NoResourcesAvailableError):
            client.create_vm(name="my-vm", cpu_cores=1, memory=512, disk_size=10)


    def test_create_vm__unauthenticated(self):
        client = Client()
        with pytest.raises(AuthenticationError):
            client.create_vm(name="my-vm", cpu_cores=1, memory=512, disk_size=10)


    def test_delete_vm(self):
        client = Client(api_key="1234")
        client.authenticate()
        result = client.delete_vm(vm_id="my-vm")
        assert result is True


    def test_delete_vm__unauthenticated(self):
        client = Client()

        with pytest.raises(AuthenticationError):
            client.delete_vm(vm_id="my-vm")
