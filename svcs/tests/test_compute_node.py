import os
import unittest
from unittest.mock import patch, MagicMock, Mock
from django.core.management import call_command
from django.urls import reverse
from svcs.management.commands.compute_node import Command
from io import StringIO

@patch.dict(os.environ, {
    'COMPUTE_NODE_NAME': 'test_node',
    'COMPUTE_NODE_TOKEN': 'test_token',
    'CONDUCTOR_API_URL': 'http://test.conductor.api',
    'RABBITMQ_HOST': 'test.rabbitmq.host',
    'HYPERVISOR_CLIENT_API_KEY': 'test_hypervisor_client_api_key',
})
class ComputeNodeCommandTests(unittest.TestCase):

    def test_initialization(self):
        command = Command()
        self.assertEqual(command.compute_node_name, 'test_node')
        self.assertEqual(command.compute_node_token, 'test_token')
        self.assertEqual(command.conductor_api_url, 'http://test.conductor.api')
        self.assertEqual(command.rabbitmq_host, 'test.rabbitmq.host')

    @patch('sys.stdout', new_callable=StringIO)
    @patch('requests.patch')
    def test_virtual_machine_update_state_success(self, mock_patch, mock_stdout):
        command = Command()
        mock_patch.return_value.status_code = 200
        command.virtual_machine_update_state('vm1', 'hypervisor_id', 'started')
        mock_patch.assert_called_once()
        output = mock_stdout.getvalue()
        self.assertIn('Successfully notified conductor about state change for VM vm1', output)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('requests.patch')
    def test_virtual_machine_update_state_failure(self, mock_patch, mock_stdout):
        command = Command()
        mock_patch.return_value.status_code = 400
        with self.assertRaises(Exception):
            command.virtual_machine_update_state('vm1', 'hypervisor_id', 'started')
        output = mock_stdout.getvalue()

    @patch('sys.stdout', new_callable=StringIO)
    @patch('pika.BlockingConnection')
    def test_handle(self, mock_blocking_connection, mock_stdout):
        command = Command()
        mock_channel = MagicMock()
        mock_blocking_connection.return_value.channel.return_value = mock_channel
        mock_channel.basic_consume.side_effect = lambda queue, on_message_callback, auto_ack: on_message_callback(
            ch=mock_channel, method=Mock(), properties=Mock(), body=b'{"id": "vm1", "state": "started"}'
        )
        with patch.object(command, 'virtual_machine_update_state') as mock_update_state:
            command.handle()
            mock_channel.basic_consume.assert_called()
            mock_channel.start_consuming.assert_called()
        output = mock_stdout.getvalue()
        self.assertIn('Starting RabbitMQ listener on compute node test_node...', output)
        self.assertIn('test_node: received b\'{"id": "vm1", "state": "started"}\' with routing key', output)
        self.assertIn('Waiting for messages. To exit press CTRL+C', output)

if __name__ == '__main__':
    unittest.main()
