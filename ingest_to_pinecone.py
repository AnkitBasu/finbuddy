#!/usr/bin/env python3
"""
Standalone script to ingest JSONL files into Pinecone vector DB.

Usage:
    python ingest_to_pinecone.py

Ensure PINECONE_API_KEY is set in your .env file before running.
"""

import sys
import os

# Add project root to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.vector_store import run_full_ingestion

if __name__ == "__main__":
    run_full_ingestion()
