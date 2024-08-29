import logging
import random

from uuid import uuid4

from .exceptions import AuthenticationError, NoResourcesAvailableError
from .models import VirtualMachine

logger = logging.getLogger()


class Client:
    """
    A mock client to manage virtual machines
    """

    api_key: str | None
    authenticated: bool = False

    def __init__(self, api_key: str = None):
        self.api_key = api_key

    def authenticate(self) -> bool:
        """
        Authenticate

        Returns:
            bool if authenticated
        """
        if not self.api_key:
            raise AuthenticationError("Invalid API key")

        self.authenticated = True
        return self.authenticated

    def create_vm(
        self,
        name: str,
        cpu_cores: int,
        memory: int,
        disk_size: int,
        public_ip: str | None = None,
        labels: list[str] = None,
    ) -> VirtualMachine:
        """
        Create a Virtual Machine

        Args:
            name: str of VM name
            cpu_cores: int of VM CPU cores
            memory: int of VM memory
            disk_size: int of VM disk size
            public_ip: optional str of public IP to assign
            labels: optional list of label strings

        Returns:
            the created VirtualMachine object
        """
        if not self.authenticated:
            raise AuthenticationError("Not authenticated")

        if random.randint(1, 100) == 1:
            # simulate no resources 1% of the time
            raise NoResourcesAvailableError(
                "No resources available to create a new virtual machine"
            )

        vm_id = f"{uuid4()}"
        logger.info(f"Creating VM with ID {vm_id}")

        return VirtualMachine(
            id=vm_id,
            name=name,
            cpu_cores=cpu_cores,
            memory=memory,
            disk_size=disk_size,
            public_ip=public_ip,
            labels=labels or [],
        )

    def delete_vm(self, vm_id: str) -> bool:
        """
        Delete a Virtual Machine

        Args:
            vm_id: str of VM ID

        Returns:
            bool if deleted
        """
        if not self.authenticated:
            raise AuthenticationError("Not authenticated")

        logger.info(f"Deleting VM with ID {vm_id}")
        return True
