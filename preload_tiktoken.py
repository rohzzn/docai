#!/usr/bin/env python3
# Script to preload tiktoken BPE files before starting the application

import tiktoken
import sys

def preload_tiktoken_files():
    """Preload tiktoken BPE files to avoid download issues at runtime"""
    print("Preloading tiktoken files...")
    try:
        # Load cl100k_base which is used by OpenAI embeddings
        _ = tiktoken.get_encoding("cl100k_base")
        print("✓ Successfully preloaded cl100k_base encoding")
        
        # Also preload other common encodings
        _ = tiktoken.encoding_for_model("text-embedding-ada-002")
        print("✓ Successfully preloaded text-embedding-ada-002 model encoding")
        
        _ = tiktoken.encoding_for_model("gpt-3.5-turbo")
        print("✓ Successfully preloaded gpt-3.5-turbo model encoding")
        
        return True
    except Exception as e:
        print(f"Error preloading tiktoken files: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    success = preload_tiktoken_files()
    sys.exit(0 if success else 1) 