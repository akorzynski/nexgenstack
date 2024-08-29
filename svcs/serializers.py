from adrf.serializers import Serializer
from rest_framework import serializers
from .models import (
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
from django.shortcuts import aget_object_or_404
from django.db.models import Subquery


class VirtualMachineSerializer(Serializer):
    environment_name = serializers.CharField(max_length=255)
    image_name = serializers.CharField(max_length=255)
    key_names = serializers.ListField(
        child=serializers.CharField(max_length=255), min_length=1
    )
    flavor_name = serializers.CharField(max_length=255)
    name = serializers.CharField(max_length=255, required=False)  # Make this optional
    user_data = serializers.CharField(max_length=1024 * 1024, required=False)
    callback_url = serializers.URLField(required=False)
    assign_floating_ip = serializers.BooleanField(default=False)
    labels = serializers.ListField(
        child=serializers.CharField(max_length=255), required=False, allow_empty=True
    )

    async def acreate(self, validated_data):
        user = self.context["user"]
        group = await user.groups.afirst() if await user.groups.aexists() else None
        if group is None:
            raise serializers.ValidationError(
                {"error": "User does not belong to any group."}
            )
        environment = await aget_object_or_404(
            Environment, name=validated_data["environment_name"], group=group
        )
        image = await aget_object_or_404(Image, name=validated_data["image_name"])
        flavor = await aget_object_or_404(Flavor, name=validated_data["flavor_name"])

        compute_node = await self.select_compute_node()

        vm = await VirtualMachine.objects.acreate(
            name=validated_data.get("name"),
            environment=environment,
            image=image,
            flavor=flavor,
            user_data=validated_data.get("user_data"),
            callback_url=validated_data.get("callback_url"),
            compute_node=compute_node,
        )

        try:
            public_ip = await self.assign_floating_ip_if_requested(
                vm, validated_data["assign_floating_ip"]
            )
            await self.create_vm_key_bindings(vm, validated_data.get("key_names", []))
            await self.create_vm_labels(vm, validated_data.get("labels", []))
        except Exception as e:
            await vm.adelete()
            raise e

        return vm, public_ip

    async def assign_floating_ip_if_requested(self, vm, assign_floating_ip):
        if not assign_floating_ip:
            return None
        available_ip_subquery = (
            FloatingIP.objects.filter(virtual_machine__isnull=True)
            .order_by("id")
            .values("id")[:1]
        )
        updated_count = await FloatingIP.objects.filter(
            id=Subquery(available_ip_subquery)
        ).aupdate(virtual_machine=vm)
        if updated_count == 0:
            raise serializers.ValidationError(
                {"error": "No unused floating IPs are available."}
            )
        floating_ip = await aget_object_or_404(FloatingIP, virtual_machine=vm)
        return floating_ip.ip_address

    async def create_vm_key_bindings(self, vm, key_names):
        for key_name in key_names:
            key = await aget_object_or_404(Key, environment=vm.environment, name=key_name)
            await VMKeyBinding.objects.acreate(virtual_machine=vm, key=key)

    async def create_vm_labels(self, vm, labels):
        for label in labels:
            await VMLabel.objects.acreate(virtual_machine=vm, name=label)

    async def select_compute_node(self):
        # TODO: Implement a scheduling algorithm to select the best compute node
        # For now, just select a random compute node
        compute_node = await ComputeNode.objects.order_by("?")[:1].afirst()
        return compute_node
