from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from environs import Env
from pocketbase_utils import (
    initialize_pocketbase_client,
    get_filtered_collection,
    get_full_collection,
    download_application_template,
    upload_processed_application,
)

from excel_utils import update_excel_sheet

# Configure logging
logging.basicConfig(
    filename="fastapi_log.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Load environment variables and initialize PocketBase client once at startup
env = Env()
env.read_env()
logging.info("Load the environment variables")
POCKETBASE_URL = env.str("POCKETBASE_URL")
client = initialize_pocketbase_client(POCKETBASE_URL)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow Nuxt dev server
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


@app.get("/fillingForm")
async def filling_form():
    """Process an uploaded form by filling an Excel template and updating PocketBase."""
    logging.info("Starting script execution")
    env = Env()
    env.read_env()

    logging.info("Load the environment variables")
    POCKETBASE_URL = env.str("POCKETBASE_URL")

    client = initialize_pocketbase_client(POCKETBASE_URL)

    # A queue contains several records.A record contains several fields.One of the fields is form_data.
    project_records = get_filtered_collection(
        client, "projects", query_params={"filter": 'status="uploaded"'}
    )

    if project_records:
        logging.info("Pop out the record")
        first_uploaded_record = project_records[0]

        logging.info("Pop out the form data")
        form_data = first_uploaded_record.form_data

        logging.info("Download the transfer table from pockethost")
        cell_table_records = get_full_collection(client, "cellTable")
        cell_table_dict = {
            record.name: record.cell_index for record in cell_table_records
        }

        logging.info("Merge the form data with transfer table")
        excel_sheet_content = {}
        for name, cell_index in cell_table_dict.items():
            if name in form_data["software"]:
                excel_sheet_content[cell_index] = form_data["software"][name]

        logging.info("Download application template from Pocketbase")
        application_template = download_application_template(
            client, version="v2"
        )  # Specify version

        if application_template:
            logging.info("Write the table content into Excel sheet")
            updated_application = update_excel_sheet(
                application_template, excel_sheet_content
            )

            if updated_application:
                logging.info("Upload application to Pocketbase")
                record_id = first_uploaded_record.id
                response = upload_processed_application(
                    client, record_id, updated_application
                )
                logging.info(response)
                message, file_url = upload_processed_application(
                    client, record_id, updated_application
                )
                logging.info(message)
                if file_url:
                    return {
                        "status": "success",
                        "record_id": record_id,
                        "file_url": file_url,
                    }
                else:
                    return {"status": "error", "message": "Upload failed"}

            else:
                logging.error("Failed to update Excel sheet")
                return {"status": "error", "message": "Failed to update Excel sheet"}

        else:
            logging.error("Failed to download application template")

    return {"status": "error", "message": "No records to process"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
