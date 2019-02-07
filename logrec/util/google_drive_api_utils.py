from __future__ import print_function
import os

import httplib2
from googleapiclient import discovery
from googleapiclient.http import MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

# FIXME

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = '/home/hlib/thesis/log-recommender/client_secret.json'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'drive-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = 'vocab-modeling-data'
        credentials = tools.run_flow(flow, store, None)
        print('Storing credentials to ' + credential_path)
    return credentials


def uploadToGoogle(filename):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    drive_service = discovery.build('drive', 'v3', http=http)
    files = drive_service.files()
    file_counter = 0

    print(f"Uploading file {file_counter} to Google drive")
    file_metadata = {
        'name': filename,
        'mimeType': "application/zip"
    }
    media = MediaFileUpload(filename,
                            mimetype='application/zip',
                            resumable=True)
    files.create(body=file_metadata, media_body=media).execute()


if __name__ == '__main__':
    uploadToGoogle("/home/hlib/t.zip")
