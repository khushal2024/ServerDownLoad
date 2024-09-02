from flask import Flask, request, send_file, jsonify
import yt_dlp
import io
import os
import traceback
from uuid import uuid4

app = Flask(__name__)

TEMP_DIR = 'temp_downloads'

# Ensure the temporary directory exists
os.makedirs(TEMP_DIR, exist_ok=True)

def get_mime_type(file_extension):
    mime_types = {
        'mp4': 'video/mp4',
        'webm': 'video/webm',
        'mkv': 'video/x-matroska',
        'avi': 'video/x-msvideo',
        'mov': 'video/quicktime',
        'flv': 'video/x-flv',
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'ogg': 'audio/ogg',
        'pdf': 'application/pdf',
        'txt': 'text/plain',
    }
    return mime_types.get(file_extension, 'application/octet-stream')

def download_content(url):
    unique_id = uuid4().hex
    temp_filename = f'{unique_id}.tmp'
    temp_filepath = os.path.join(TEMP_DIR, temp_filename)

    ydl_opts = {
        'format': 'best',
        'outtmpl': temp_filepath,
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_extension = info_dict.get('ext', 'tmp')
            filename = f"{info_dict.get('title', 'download')}.{file_extension}"
            
            # Log the extracted information for debugging
            print(f"Extracted info: {info_dict}")

            # Read the downloaded file into BytesIO
            with open(temp_filepath, 'rb') as f:
                file_data = io.BytesIO(f.read())
            
            file_data.seek(0)

    except Exception as e:
        print("Exception occurred: ", str(e))
        print(traceback.format_exc())
        raise e
    
    return file_data, filename, temp_filepath, file_extension

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL not provided'}), 400

    try:
        file_data, filename, temp_filepath, file_extension = download_content(url)
        response = send_file(
            file_data,
            as_attachment=True,
            download_name=filename,
            mimetype=get_mime_type(file_extension)
        )

        # Clean up the temporary file after sending the response
        os.remove(temp_filepath)
        
        return response
    except Exception as e:
        print("Exception occurred: ", str(e))
        print(traceback.format_exc())
        # Ensure file is removed in case of error
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
