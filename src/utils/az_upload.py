import os
import requests
import logging
from typing import Dict, List, Optional, Union
from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv

load_dotenv()

# Logging Configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)


def upload_image_to_blob(
    container_name: str,
    farm_id: str,
    date: str,
    image_name_type: str,
    image_file: Union[str, bytes],
    file_extension: str = 'png'
) -> dict:
    """
    Upload an image to Azure Blob Storage and return its URL.
    """
    logger.info(f"Uploading image for farm_id={farm_id}, date={date}, type={image_name_type}")
    
    try:
        connection_string = os.getenv("AZURE_CONNECTION_STRING")

        if not connection_string:
            logger.error("Missing AZURE_CONNECTION_STRING environment variable")
            raise Exception("Cannot Upload images currently")

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)

        if file_extension is None:
            if isinstance(image_file, str):
                from pathlib import Path
                file_extension = Path(image_file).suffix.lstrip('.')
                if not file_extension:
                    logger.error("File extension could not be determined from path")
                    return {'success': False, 'url': None, 'error': 'Could not determine file extension from file path'}
            else:
                logger.error("file_extension must be provided when uploading bytes")
                return {'success': False, 'url': None, 'error': 'file_extension must be provided when uploading bytes'}

        file_extension = file_extension.lstrip('.')
        blob_path = f"{farm_id}/{date}/{image_name_type}.{file_extension}"
        blob_client = container_client.get_blob_client(blob_path)

        # Determine content type
        content_type_map = {
            'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
            'gif': 'image/gif', 'bmp': 'image/bmp', 'webp': 'image/webp'
        }
        content_type = content_type_map.get(file_extension.lower(), 'application/octet-stream')
        content_settings = ContentSettings(content_type=content_type)

        if isinstance(image_file, str):
            if not os.path.exists(image_file):
                logger.error(f"File not found: {image_file}")
                return {'success': False, 'url': None, 'error': f'File not found: {image_file}'}
            with open(image_file, 'rb') as data:
                blob_client.upload_blob(data, overwrite=True, content_settings=content_settings)
        else:
            blob_client.upload_blob(image_file, overwrite=True, content_settings=content_settings)

        logger.info(f"Upload successful for {image_name_type} → {blob_client.url}")
        return {'success': True, 'url': blob_client.url, 'error': None}

    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        return {'success': False, 'url': None, 'error': f'File not found: {str(e)}'}

    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        return {'success': False, 'url': None, 'error': f'Permission denied: {str(e)}'}

    except ValueError as e:
        logger.error(f"Invalid value: {e}")
        return {'success': False, 'url': None, 'error': f'Invalid value: {str(e)}'}

    except Exception as e:
        logger.exception(f"Upload failed: {type(e).__name__} - {e}")
        return {'success': False, 'url': None, 'error': f'Upload failed: {type(e).__name__} - {str(e)}'}


def upload_field_images_to_azure(
    field_data: dict,
    exclude_types: List[str] = None
) -> Dict[str, any]:
    """
    Download images from Google Cloud Storage URLs and upload them to Azure Blob Storage.
    """
    container_name = "farm-images"
    if exclude_types is None:
        exclude_types = []

    meta = field_data.get('_meta', {})
    field_id = meta.get('field_id', 'unknown_field')
    sensed_day = meta.get('sensed_day', 'unknown_date')
    timestamp = meta.get('timestamp', '')

    logger.info(f"Starting upload for field_id={field_id}, sensed_day={sensed_day}")

    azure_urls = {}
    upload_details = {}
    successful_uploads = 0
    failed_uploads = 0

    for image_type, url in field_data.items():
        if image_type == '_meta':
            continue

        if image_type in exclude_types:
            logger.info(f"Skipping excluded type: {image_type}")
            upload_details[image_type] = {
                'success': False, 'error': 'Excluded by user', 'skipped': True
            }
            continue

        try:
            logger.info(f"Downloading {image_type} from {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            image_bytes = response.content
            content_type = response.headers.get('content-type', '')

            if 'png' in content_type:
                file_extension = 'png'
            elif 'jpeg' in content_type or 'jpg' in content_type:
                file_extension = 'jpg'
            else:
                file_extension = 'png'

            result = upload_image_to_blob(
                container_name=container_name,
                farm_id=field_id,
                date=sensed_day,
                image_name_type=image_type,
                image_file=image_bytes,
                file_extension=file_extension
            )

            if result['success']:
                azure_urls[image_type] = result['url']
                successful_uploads += 1
                logger.info(f"✓ {image_type} uploaded successfully to {result['url']}")
            else:
                failed_uploads += 1
                logger.error(f"✗ {image_type} upload failed: {result['error']}")

            upload_details[image_type] = result

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download {image_type}: {e}")
            failed_uploads += 1
            upload_details[image_type] = {
                'success': False, 'url': None, 'error': f'Download failed: {str(e)}'
            }

        except Exception as e:
            logger.exception(f"Unexpected error during {image_type} upload: {e}")
            failed_uploads += 1
            upload_details[image_type] = {
                'success': False, 'url': None, 'error': f'Unexpected error: {str(e)}'
            }

    response = {
        **azure_urls,
        '_meta': {
            'field_id': field_id,
            'sensed_day': sensed_day,
            'timestamp': timestamp,
            'total_images': len([k for k in field_data.keys() if k != '_meta']),
            'successful_uploads': successful_uploads,
            'failed_uploads': failed_uploads,
            'container_name': container_name
        },
        '_upload_details': upload_details
    }

    logger.info(f"Upload complete for {field_id}: {successful_uploads} success, {failed_uploads} failed")
    return response


# def print_upload_summary(results: Dict[str, any]):
#     """Print a summary of upload results."""
#     meta = results.get('_meta', {})
#     upload_details = results.get('_upload_details', {})

#     total = meta.get('total_images', 0)
#     successful = meta.get('successful_uploads', 0)
#     failed = meta.get('failed_uploads', 0)

#     logger.info(f"Printing upload summary for {meta.get('field_id', 'N/A')}")
#     print("\n" + "="*70)
#     print(f"UPLOAD SUMMARY")
#     print("="*70)
#     print(f"Field ID: {meta.get('field_id', 'N/A')}")
#     print(f"Date: {meta.get('sensed_day', 'N/A')}")
#     print(f"Container: {meta.get('container_name', 'N/A')}")
#     print("-"*70)
#     print(f"Total images: {total}")
#     print(f"Successful: {successful}")
#     print(f"Failed: {failed}")
#     print("="*70)

#     if failed > 0:
#         print("\nFailed uploads:")
#         for image_type, detail in upload_details.items():
#             if not detail.get('success', False):
#                 print(f"  - {image_type}: {detail.get('error', 'Unknown error')}")

#     if successful > 0:
#         print("\nSuccessful uploads (Azure URLs):")
#         for image_type in upload_details.keys():
#             if upload_details[image_type].get('success', False):
#                 url = results.get(image_type, 'N/A')
#                 print(f"  - {image_type}: {url}")

#     print("\n")


# def save_urls_to_json(results: Dict[str, any], output_file: str = 'azure_urls.json'):
#     """Save the Azure URLs to a JSON file for frontend consumption."""
#     import json
#     logger.info(f"Saving Azure URLs to {output_file}")

#     frontend_data = {
#         k: v for k, v in results.items() if k != '_upload_details'
#     }

#     with open(output_file, 'w') as f:
#         json.dump(frontend_data, f, indent=2)

#     logger.info(f"Azure URLs saved to {output_file}")
#     print(f"Azure URLs saved to {output_file}")
