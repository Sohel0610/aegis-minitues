from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.client_credential import ClientCredential
import os
from urllib.parse import quote

# Hard-coded values
site_url = "https://adaniltd.sharepoint.com/sites/AGEL-AWMS5SImplementation"
client_id = "125aac18-c8bf-4c93-8412-56e697bff445"
client_secret = "SWNYOFF+SldsRjA5OVFKNWcwX3Ezc0I4Ry5lUUFOdUJxMW9xRmF3Tw=="

def log_message(log_path, message):
    try:
        with open(log_path, "a") as log_file:
            log_file.write(message + "\n")
            log_file.flush()  # Ensure the message is written to the file
    except Exception as e:
        print(f"Failed to write log: {e}")

# Connect to SharePoint
credentials = ClientCredential(client_id, client_secret)
ctx = ClientContext(site_url).with_credentials(credentials)

def download_files_from_sharepoint(sharepoint_folder_url, local_folder_path, log_path):
    try:
        # Encode the URL
        encoded_folder_url = quote(sharepoint_folder_url)
        
        log_message(log_path, "Connecting to SharePoint...")
        folder = ctx.web.get_folder_by_server_relative_url(encoded_folder_url)
        files = folder.files.get().execute_query()
        log_message(log_path, f"Found {len(files)} files in the folder.")
        
        if not os.path.exists(local_folder_path):
            os.makedirs(local_folder_path)
        
        for file in files:
            file_name = file.properties["Name"]
            file_url = file.properties["ServerRelativeUrl"]
            local_file_path = os.path.join(local_folder_path, file_name)
            log_message(log_path, f"Downloading {file_name}...")
            with open(local_file_path, "wb") as local_file:
                response = ctx.web.get_file_by_server_relative_url(file_url).download(local_file).execute_query()
            log_message(log_path, f"Downloaded {file_name} to {local_folder_path}")
    except Exception as e:
        log_message(log_path, f"An error occurred: {e}")

def main(params):
    if len(params) < 2:
        print("Error: Not enough parameters provided.")
        return

    sharepoint_folder_url = params[0]
    local_folder_path = params[1]
    log_path = params[2]
    
    download_files_from_sharepoint(sharepoint_folder_url, local_folder_path, log_path)