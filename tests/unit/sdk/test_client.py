import pytest

from unittest.mock import patch

from sdk import Client
from sdk.exceptions import AuthenticationError, NoResourcesAvailableError
from sdk.models import VirtualMachine


def test_authenticate():
    client = Client(api_key="1234")
    client.authenticate()
    assert client.authenticated is True


def test_authenticate__without_api_key():
    client = Client(api_key=None)
    with pytest.raises(AuthenticationError):
        client.authenticate()


@patch("sdk.client.uuid4", return_value="uuid4")
@patch("sdk.client.random.randint", return_value=0)
def test_create_vm(mock_randint, mock_uuid4):
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


@patch("sdk.client.random.randint", return_value=1)
def test_create_vm__fails_with_no_resources_available(mock_randint):
    client = Client(api_key="1234")
    client.authenticate()

    with pytest.raises(NoResourcesAvailableError):
        client.create_vm(name="my-vm", cpu_cores=1, memory=512, disk_size=10)


def test_create_vm__unauthenticated():
    client = Client()
    with pytest.raises(AuthenticationError):
        client.create_vm(name="my-vm", cpu_cores=1, memory=512, disk_size=10)


def test_delete_vm():
    client = Client(api_key="1234")
    client.authenticate()
    result = client.delete_vm(vm_id="my-vm")
    assert result is True


def test_delete_vm__unauthenticated():
    client = Client()

    with pytest.raises(AuthenticationError):
        client.delete_vm(vm_id="my-vm")
