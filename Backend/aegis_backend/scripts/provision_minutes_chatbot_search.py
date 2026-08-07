"""Provision/update the Azure AI Search schema for the Minutes Chatbot.

Run only from a secured deployment environment with AZURE_SEARCH_ADMIN_KEY set.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chatbot_minutes.services.azure_search_indexer import AzureSearchIndexer


if __name__ == "__main__":
    AzureSearchIndexer().ensure_index()
    print("Minutes Chatbot Azure AI Search index provisioned successfully.")
