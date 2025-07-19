#!/usr/bin/env python3
"""
Upload downloaded files to Turbopuffer using TurbopufferManager
"""

import os
import glob
from lib.turbopuffer_manager import TurbopufferManager


def main():
    """Main function to upload the latest downloaded files"""
    
    # Check for required environment variables
    if not os.getenv("TURBOPUFFER_API_KEY"):
        print("❌ TURBOPUFFER_API_KEY environment variable is required")
        print("Get your API key from: https://turbopuffer.com/dashboard")
        return
    
    # Find the latest downloads directory
    downloads_base = "downloads"
    if not os.path.exists(downloads_base):
        print(f"❌ Downloads directory '{downloads_base}' not found")
        return
    
    # Find the most recent download directory
    download_dirs = glob.glob(os.path.join(downloads_base, "circle-chat-agents_*"))
    if not download_dirs:
        print("❌ No download directories found")
        return
    
    # Sort by modification time and get the latest
    latest_dir = max(download_dirs, key=os.path.getmtime)
    repo_url = "https://github.com/uriafranko/circle-chat-agents"  # From main.py
    
    print(f"Using downloads directory: {latest_dir}")
    
    # Initialize manager and upload
    try:
        manager = TurbopufferManager()
        success = manager.upload_files(latest_dir, repo_url)
        
        if success:
            print("✅ Upload completed successfully!")
            
            # Test search functionality
            print("\n🔍 Testing search functionality...")
            results = manager.search_by_text(repo_url, "API", top_k=3)
            print(f"Found {len(results)} results for 'API':")
            for result in results:
                print(f"  - {result['file_name']} (score: {result['score']:.4f})")
        else:
            print("❌ Upload failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
