import sys

__author__ = 'hlib'

def upload_to_google(dir):
    import os
    import httplib2
    from googleapiclient import discovery
    from googleapiclient.http import MediaFileUpload
    from google_drive_api_utils import get_credentials

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    drive_service = discovery.build('drive', 'v3', http=http)
    files = drive_service.files()
    file_counter = 0
    for filename in os.listdir(dir):
        file_counter += 1
        print("Uploading file " + str(file_counter) + " to Google drive...")
        file_metadata = {
            'name': filename,
            'mimeType': 'application/vnd.google-apps.spreadsheet'
        }
        media = MediaFileUpload(os.path.join(dir, filename),
                                mimetype='text/csv',
                                resumable=True)
        files.create(body=file_metadata, media_body=media).execute()

if __name__ == '__name__':
    upload_to_google(sys.argv[0])