import logging
from pocketbase import PocketBase
from pocketbase.client import ClientResponseError
from io import BytesIO
import requests


def initialize_pocketbase_client(url):
    """Initialize a PocketBase client with the given URL."""
    return PocketBase(url)


def get_filtered_collection(client, collection_name, query_params=None):
    """Retrieve a filtered list of records from a PocketBase collection."""
    try:
        logging.info(
            f"Fetching data from collection: {collection_name} with params: {query_params}"
        )
        records = client.collection(collection_name).get_full_list(
            query_params=query_params
        )
        logging.info(f"Records fetched: {len(records)}")
        return records
    except ClientResponseError as e:
        logging.error(f"HTTP error occurred: {e}")
        return None


def get_full_collection(client, collection_name):
    """Retrieve all records from a PocketBase collection."""
    try:
        records = client.collection(collection_name).get_full_list()
        return records
    except ClientResponseError as e:
        logging.error(f"Failed to retrieve records: {e}")
        return None


def download_application_template(client: PocketBase, version: str) -> bytes:
    """
    Downloads an application template (Excel file) from PocketBase based on version.

    Args:
        client (PocketBase): Initialized PocketBase client
        version (str): Version identifier (e.g., "V0", "V1")

    Returns:
        bytes: Excel file content as bytes, or None if failed
    """
    try:
        # Query the collection for a record matching the version
        records = client.collection("software_application_base").get_full_list(
            query_params={"filter": f'version="{version}"'}
        )

        if not records:
            logging.error(f"No record found for version: {version}")
            return None

        # Assuming the first record is the desired one
        record = records[0]

        # Extract fields
        version_found = getattr(record, "version", None)
        application_template = getattr(record, "application_template", None)
        note = getattr(record, "note", None)

        if not application_template:
            logging.error(f"No application_template found for version: {version}")
            return None

        # Construct the file URL (PocketBase file URL pattern)
        file_url = f"{client.base_url}/api/files/{record.collection_id}/{record.id}/{application_template}"

        # Download the file content
        response = client.http_client.get(file_url)
        response.raise_for_status()  # Raise an error for bad status codes

        # Return the file content as bytes (stays in RAM)
        file_content = response.content
        logging.info(f"Downloaded application_template for version: {version}")
        return file_content

    except ClientResponseError as e:
        logging.error(f"Failed to download file from PocketBase: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error during file download: {e}")
        return None


def upload_processed_application(
    client: PocketBase, record_id: str, application: bytes
) -> str:
    """
    Uploads a processed Excel file to PocketBase and updates the record status using a multipart request.

    Args:
        client (PocketBase): Initialized PocketBase client
        record_id (str): ID of the record to update
        application (bytes): Processed Excel file content as bytes

    Returns:
        str: Success or error message
    """
    try:
        url = f"{client.base_url}/api/collections/projects/records/{record_id}"
        data = {"status": "processed"}
        file_name = f"processed_application_{record_id}.xlsx"
        file_content = BytesIO(application)
        files = {
            "application": (
                file_name,
                file_content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }
        # Perform the upload
        response = requests.patch(
            url,
            data=data,
            files=files,
            headers=(
                {"Authorization": client.auth_store.token}
                if client.auth_store.token
                else {}
            ),
        )
        response.raise_for_status()

        # Fetch the updated record to get the exact filename
        updated_record_response = client.collection("projects").get_one(record_id)
        actual_filename = (
            updated_record_response.application
        )  # Use the filename PocketBase assigned
        file_url = f"{client.base_url}/api/files/projects/{record_id}/{actual_filename}"

        message = f"Application uploaded and record {record_id} status updated to 'processed'. File URL: {file_url}"
        logging.info(message)
        return message, file_url

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to upload file to PocketBase: {e}")
        return f"Error uploading application: {e}", None
    except Exception as e:
        logging.error(f"Unexpected error during file upload: {e}")
        return f"Unexpected error: {e}", None
