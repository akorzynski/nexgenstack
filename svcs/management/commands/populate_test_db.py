from django.core.management.base import BaseCommand
from svcs.tests.test_conductor import VirtualMachineViewTests

class Command(BaseCommand):
    help = 'Populate the test database with initial data'

    def handle(self, *args, **kwargs):
        tests = VirtualMachineViewTests()
        tests.setUp()
        self.stdout.write(self.style.SUCCESS('Successfully populated the test database'))
