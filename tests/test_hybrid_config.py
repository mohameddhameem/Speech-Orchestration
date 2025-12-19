import os
import unittest
from unittest.mock import patch, MagicMock
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "speech-flow-backend"))

from messaging_adapter import get_message_broker, AzureServiceBusAdapter, RabbitMQAdapter
from storage_adapter import get_storage_adapter, AzureBlobStorageAdapter, LocalFileStorageAdapter

class TestHybridConfiguration(unittest.TestCase):

    @patch.dict(os.environ, {
        "ENVIRONMENT": "LOCAL",
        "USE_CLOUD_RESOURCES": "true",
        "AZURE_CLIENT_ID": "fake-client-id",
        "AZURE_CLIENT_SECRET": "fake-secret",
        "AZURE_TENANT_ID": "fake-tenant",
        "SERVICEBUS_NAMESPACE": "test-ns"
    })
    @patch("messaging_adapter.AzureServiceBusAdapter")
    def test_messaging_adapter_hybrid_spn(self, mock_sb_adapter):
        """Test that Service Bus is used in LOCAL mode when USE_CLOUD_RESOURCES is true and SPN is provided."""
        broker = get_message_broker()
        # Should return an AzureServiceBusAdapter
        mock_sb_adapter.assert_called_once()
        # Verify it was called with use_connection_string=False (meaning DefaultAzureCredential)
        call_args = mock_sb_adapter.call_args
        self.assertFalse(call_args.kwargs.get('use_connection_string'))
        self.assertEqual(call_args.kwargs.get('fully_qualified_namespace'), "test-ns.servicebus.windows.net")

    @patch.dict(os.environ, {
        "ENVIRONMENT": "LOCAL",
        "USE_CLOUD_RESOURCES": "true",
        "AZURE_CLIENT_ID": "fake-client-id",
        "AZURE_CLIENT_SECRET": "fake-secret",
        "AZURE_TENANT_ID": "fake-tenant",
        "AZURE_STORAGE_ACCOUNT_NAME": "test-account"
    })
    @patch("storage_adapter.AzureBlobStorageAdapter")
    def test_storage_adapter_hybrid_spn(self, mock_blob_adapter):
        """Test that Azure Blob Storage is used in LOCAL mode when USE_CLOUD_RESOURCES is true and SPN is provided."""
        storage = get_storage_adapter()
        mock_blob_adapter.assert_called_once()
        # Verify it was called with use_connection_string=False (meaning DefaultAzureCredential)
        call_args = mock_blob_adapter.call_args
        self.assertFalse(call_args.kwargs.get('use_connection_string'))
        self.assertEqual(call_args.kwargs.get('account_url'), "https://test-account.blob.core.windows.net")


if __name__ == "__main__":
    unittest.main()
