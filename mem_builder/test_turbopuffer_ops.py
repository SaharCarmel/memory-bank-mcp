#!/usr/bin/env python3
"""
Test script for Turbopuffer namespace operations
- Delete namespaces
- Fetch all items in a namespace
"""

import os
import sys
from lib.turbopuffer_manager import TurbopufferManager
from lib.logger import get_logger
from dotenv import load_dotenv

def main():
    """Main function to test Turbopuffer operations"""
    logger = get_logger("test_turbopuffer")
    
    # Load environment variables
    load_dotenv()
    
    # Initialize TurbopufferManager
    try:
        tpuf_manager = TurbopufferManager()
        logger.info("TurbopufferManager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize TurbopufferManager: {e}")
        sys.exit(1)
    
    # Test repository URL (replace with actual repo URL for testing)
    test_repo_url = input("Enter repository URL to test (or press Enter for default): ").strip()
    if not test_repo_url:
        test_repo_url = "https://github.com/uriafranko/circle-chat-agents"
    
    while True:
        print("\n=== Turbopuffer Namespace Operations ===")
        print("1. Fetch all items in namespace")
        print("2. Search files in namespace")
        print("3. Delete namespace")
        print("4. Exit")
        
        choice = input("Select an option (1-4): ").strip()
        
        if choice == "1":
            # Fetch all items in namespace
            print(f"Fetching all items for repository: {test_repo_url}")
            try:
                items = tpuf_manager.get_all_files(test_repo_url)
                
                if items:
                    print(f"\nFound {len(items)} items in namespace:")
                    print("-" * 50)
                    for i, item in enumerate(items, 1):
                        print(f"{i}. File: {item.get('file_name', 'Unknown')}")
                        print(f"   ID: {item.get('id', 'Unknown')}")
                        content_preview = item.get('content', '')[:100]
                        if len(content_preview) == 100:
                            content_preview += "..."
                        print(f"   Content preview: {content_preview}")
                        print("-" * 50)
                else:
                    print("No items found in namespace.")
                    
            except Exception as e:
                logger.error(f"Error fetching items: {e}")
                print(f"Error: {e}")
        
        elif choice == "2":
            # Search files in namespace
            query = input("Enter search query: ").strip()
            if not query:
                print("Search query cannot be empty.")
                continue
                
            print(f"Searching for '{query}' in repository: {test_repo_url}")
            try:
                results = tpuf_manager.search_files(test_repo_url, query)
                
                if results:
                    print(f"\nFound {len(results)} matching items:")
                    print("-" * 50)
                    for i, result in enumerate(results, 1):
                        print(f"{i}. File: {result.get('file_name', 'Unknown')}")
                        print(f"   ID: {result.get('id', 'Unknown')}")
                        print(f"   Score: {result.get('hybrid_score', result.get('distance', 'N/A'))}")
                        content_preview = result.get('content', '')[:150]
                        if len(content_preview) == 150:
                            content_preview += "..."
                        print(f"   Content preview: {content_preview}")
                        print("-" * 50)
                else:
                    print("No matching items found.")
                    
            except Exception as e:
                logger.error(f"Error searching files: {e}")
                print(f"Error: {e}")
        
        elif choice == "3":
            # Delete namespace
            print(f"\nWARNING: This will delete ALL data for repository: {test_repo_url}")
            confirm = input("Are you sure? Type 'yes' to confirm: ").strip().lower()
            
            if confirm == "yes":
                logger.info(f"Deleting namespace for repository: {test_repo_url}")
                try:
                    success = tpuf_manager.delete_namespace(test_repo_url)
                    if success:
                        print("Namespace deleted successfully!")
                    else:
                        print("Failed to delete namespace.")
                except Exception as e:
                    logger.error(f"Error deleting namespace: {e}")
                    print(f"Error: {e}")
            else:
                print("Deletion cancelled.")
        
        elif choice == "4":
            print("Exiting...")
            break
        
        else:
            print("Invalid choice. Please select 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()
