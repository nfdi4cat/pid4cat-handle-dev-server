#!/usr/bin/env python3
"""
Comprehensive Handle creation examples using PyHandle library
"""

from pyhandle.clientcredentials import PIDClientCredentials
from pyhandle.handleclient import PyHandleClient
import json


def create_handles():
    """Create various types of handles"""
    try:
        # Load credentials
        print("Loading credentials...")
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cred_path = os.path.join(script_dir, "credentials.json")
        cred = PIDClientCredentials.load_from_JSON(cred_path)

        # Create REST client
        print("Creating REST client...")
        client = PyHandleClient("rest").instantiate_with_credentials(cred)

        print("=" * 60)
        print("HANDLE CREATION EXAMPLES")
        print("=" * 60)

        # Example 1: Simple URL handle
        print("\n1. Creating simple URL handle...")
        handle1 = "TEST/EXAMPLE001"
        url1 = "https://example.org/dataset1"
        try:
            result1 = client.register_handle(handle1, url1)
            print(f"   Created: {result1}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"   Handle {handle1} already exists - retrieving existing record...")
                result1 = handle1
            else:
                raise e

        # Example 2: Handle with multiple values
        print("\n2. Creating handle with multiple values...")
        handle2 = "TEST/EXAMPLE002"
        # Use register_handle_kv for key-value pairs
        values = [
            ("URL", "https://example.org/dataset2"),
            ("EMAIL", "contact@example.org"),
            ("DESC", "A sample dataset for testing"),
        ]
        try:
            result2 = client.register_handle_kv(handle2, **dict(values))
            print(f"   Created: {result2}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"   Handle {handle2} already exists - retrieving existing record...")
                result2 = handle2
            else:
                raise e

        # Example 3: Generate handle with UUID
        print("\n3. Creating handle with auto-generated name...")
        url3 = "https://example.org/auto-generated"
        result3 = client.generate_and_register_handle("TEST", url3)
        print(f"   Created: {result3}")

        print("\n" + "=" * 60)
        print("HANDLE VERIFICATION")
        print("=" * 60)

        # Verify all created handles
        for handle in [handle1, handle2, result3]:
            print(f"\nHandle: {handle}")
            try:
                record = client.retrieve_handle_record(handle)
                print(f"   Values: {json.dumps(record, indent=6)}")
            except Exception as e:
                print(f"   Error retrieving: {e}")

        print("\n" + "=" * 60)
        print("HANDLE OPERATIONS")
        print("=" * 60)

        # Example: Modify a handle value
        print(f"\n4. Modifying URL in {handle1}...")
        new_url = "https://updated.example.org/dataset1"
        client.modify_handle_value(handle1, URL=new_url)
        print(f"   Updated URL to: {new_url}")

        # Verify the update
        updated_record = client.retrieve_handle_record(handle1)
        print(f"   New record: {json.dumps(updated_record, indent=6)}")

        print("\n✅ All handle operations completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    create_handles()
