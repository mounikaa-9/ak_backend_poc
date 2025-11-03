#!/usr/bin/env python
"""
Test script for SAS URL generation
Run from your Django project root: python test_sas.py
"""

import os
import django
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ak_backend_poc.settings')  # Change 'your_project' to your actual project name
django.setup()

# Now import your function
from heatmaps.api import generate_sas_url
from pipelines.new_profile_script import reload_logic

# def test_sas_generation():
#     """Test SAS URL generation with various scenarios"""
    
#     print("="*70)
#     print("TESTING SAS URL GENERATION")
#     print("="*70)
    
#     # Check if connection string is configured
#     connection_string = os.getenv("AZURE_CONNECTION_STRING")
#     print(f"\n1. Environment Check:")
#     print(f"   ✓ AZURE_CONNECTION_STRING exists: {bool(connection_string)}")
#     if connection_string:
#         print(f"   ✓ Connection string length: {len(connection_string)} chars")
#         print(f"   ✓ Contains AccountName: {'AccountName=' in connection_string}")
#         print(f"   ✓ Contains AccountKey: {'AccountKey=' in connection_string}")
#     else:
#         print("   ✗ AZURE_CONNECTION_STRING not found!")
#         return
    
#     # Test with a sample blob URL (replace with your actual blob URL)
#     test_blob_url = "https://aikyampoc.blob.core.windows.net/farm-images/1761901184414/20251029/bsi.png"
    
#     print(f"\n2. Testing SAS Generation:")
#     print(f"   Input URL: {test_blob_url}")
    
#     try:
#         sas_url = generate_sas_url(test_blob_url, expiry_minutes=60)
        
#         print(f"\n   ✓ SAS URL generated successfully!")
#         print(f"   URL length: {len(sas_url)} chars")
#         print(f"\n   ✓ SAS Parameters Check:")
#         print(f"      - Has '?' separator: {('?' in sas_url)}")
#         print(f"      - Has 'sig=' (signature): {('sig=' in sas_url)}")
#         print(f"      - Has 'se=' (expiry): {('se=' in sas_url)}")
#         print(f"      - Has 'sp=' (permissions): {('sp=' in sas_url)}")
#         print(f"      - Has 'sv=' (version): {('sv=' in sas_url)}")
        
#         # Show first and last parts of URL
#         print(f"\n   URL Preview:")
#         print(f"      Base: {sas_url.split('?')[0]}")
#         print(f"      Params: {sas_url.split('?')[1][:100]}...")
        
#         # Test accessibility
#         print(f"\n3. Testing URL Accessibility:")
#         import requests
#         response = requests.head(sas_url, timeout=10)
#         print(f"   Status: {response.status_code}")
#         print(f"   Success: {response.ok}")
#         if response.ok:
#             print(f"   Content-Type: {response.headers.get('content-type')}")
#             print(f"   Content-Length: {response.headers.get('content-length')} bytes")
#         else:
#             print(f"   ✗ Failed: {response.reason}")
            
#     except FileNotFoundError as e:
#         print(f"\n   ⚠ Blob not found: {e}")
#         print(f"   This is normal if testing with a non-existent blob")
        
#     except Exception as e:
#         print(f"\n   ✗ Error: {type(e).__name__}")
#         print(f"   Message: {str(e)}")
#         import traceback
#         print(f"\n   Full traceback:")
#         traceback.print_exc()
    
#     print("\n" + "="*70)
#     print("TEST COMPLETE")
#     print("="*70)


# def test_with_real_heatmap():
#     """Test with actual heatmap from database"""
#     from heatmaps.models import Heatmap
#     from farms.models import Farm
    
#     print("\n" + "="*70)
#     print("TESTING WITH REAL HEATMAP FROM DATABASE")
#     print("="*70)
    
#     # Get a sample heatmap
#     heatmap = Heatmap.objects.first()
    
#     if not heatmap:
#         print("\n   ✗ No heatmaps found in database")
#         print("   Upload a heatmap first to test")
#         return
    
#     print(f"\n   Found heatmap:")
#     print(f"   - Farm: {heatmap.farm.field_name}")
#     print(f"   - Index: {heatmap.index_type}")
#     print(f"   - Date: {heatmap.date}")
#     print(f"   - Original URL: {heatmap.image_url[:80]}...")
    
#     try:
#         sas_url = generate_sas_url(heatmap.image_url, expiry_minutes=60)
#         print(f"\n   ✓ SAS URL generated!")
#         print(f"   Length: {len(sas_url)} chars")
        
#         # Test accessibility
#         import requests
#         response = requests.head(sas_url, timeout=10)
#         print(f"\n   Accessibility test:")
#         print(f"   - Status: {response.status_code}")
#         print(f"   - Success: {'✓' if response.ok else '✗'}")
        
#         if response.ok:
#             print(f"\n   ✓ Image is accessible via SAS URL!")
#         else:
#             print(f"\n   ✗ Image not accessible: {response.reason}")
            
#     except Exception as e:
#         print(f"\n   ✗ Error: {str(e)}")
#         import traceback
#         traceback.print_exc()


# if __name__ == "__main__":
#     # Run basic test
#     test_sas_generation()
    
#     # Uncomment to test with real database heatmap
#     # test_with_real_heatmap()



if __name__ == "__main__":
    
    asyncio