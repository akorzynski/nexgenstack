from pydantic import BaseModel, Field, IPvAnyAddress


class VirtualMachine(BaseModel):
    """
    An object to represent a virtual machine
    """

    id: str
    name: str
    cpu_cores: int
    memory: int
    disk_size: int
    public_ip: IPvAnyAddress | None = None
    labels: list[str] = Field(default_factory=list)
