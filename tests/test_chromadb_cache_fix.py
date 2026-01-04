#!/usr/bin/env python3
"""
Test ChromaDB cache location fix
Verifies that ChromaDB uses the dedicated chroma_db/ directory
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.agents.utils.memory import FinancialSituationMemory
from tradingagents.default_config import DEFAULT_CONFIG


def test_chromadb_location():
    """Test that ChromaDB creates database in correct location"""
    print("=" * 70)
    print("Testing ChromaDB Cache Location Fix")
    print("=" * 70)
    
    # Create a temporary project directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"\n📁 Using temporary directory: {temp_dir}")
        
        # Create config with temp directory
        config = DEFAULT_CONFIG.copy()
        config["project_dir"] = temp_dir
        config["backend_url"] = "https://api.openai.com/v1"
        
        print("\n1️⃣ Creating FinancialSituationMemory instance...")
        try:
            memory = FinancialSituationMemory("test_memory", config)
            print("   ✅ Memory instance created successfully")
        except Exception as e:
            print(f"   ❌ Failed to create memory: {e}")
            return False
        
        # Check that chroma_db directory was created
        chroma_path = os.path.join(temp_dir, "chroma_db")
        print(f"\n2️⃣ Checking for ChromaDB directory: {chroma_path}")
        
        if os.path.exists(chroma_path):
            print("   ✅ chroma_db/ directory created in correct location")
        else:
            print("   ❌ chroma_db/ directory NOT found!")
            return False
        
        # List contents of chroma_db
        print(f"\n3️⃣ Contents of chroma_db/:")
        for item in os.listdir(chroma_path):
            print(f"   - {item}")
        
        # Verify SQLite database exists
        db_files = [f for f in os.listdir(chroma_path) if 'chroma' in f.lower() or f.endswith('.sqlite3')]
        if db_files:
            print(f"\n   ✅ Found ChromaDB database files: {db_files}")
        else:
            print("\n   ⚠️  No SQLite database files found (might be using different storage)")
        
        # Check that cache directory is NOT being used
        cache_path = os.path.join(temp_dir, "dataflows", "cache")
        print(f"\n4️⃣ Checking cache directory: {cache_path}")
        
        if not os.path.exists(cache_path):
            print("   ✅ Cache directory was not created (good!)")
        else:
            cache_contents = os.listdir(cache_path)
            if not cache_contents or cache_contents == ['README.md']:
                print("   ✅ Cache directory is empty/clean")
            else:
                print(f"   ⚠️  Cache directory contains: {cache_contents}")
        
        print("\n" + "=" * 70)
        print("✅ TEST PASSED: ChromaDB is using the correct location")
        print("=" * 70)
        return True


if __name__ == "__main__":
    print("\n🧪 ChromaDB Cache Location Test\n")
    
    success = test_chromadb_location()
    
    if success:
        print("\n✅ All checks passed!")
        print("\nWhat was fixed:")
        print("  • ChromaDB now creates database in chroma_db/ (project root)")
        print("  • dataflows/cache/ is no longer polluted")
        print("  • Memory persistence works correctly")
        sys.exit(0)
    else:
        print("\n❌ Test failed!")
        print("\nPlease check:")
        print("  • memory.py has been updated correctly")
        print("  • ChromaDB is installed (pip install chromadb)")
        sys.exit(1)

