#!/usr/bin/python3

import argparse
import io
import json
import logging
import mimetypes
import os
import sys
import uuid

from google.cloud import storage
from google.cloud import vision

MIMETYPE_PDF = 'application/pdf'

script_name = os.path.basename(__file__)
logging.basicConfig(level=logging.INFO, format=script_name + ': %(message)s')

def upload_blob(source_file_name, destination_blob_name, gcp_bucket):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(gcp_bucket)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

def detect_document(gcs_source_uri, mimetype):
    """OCR with PDF/TIFF/GIF files using the Google Vision API."""

    client = vision.ImageAnnotatorClient()

    feature = vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)

    gcs_source = vision.GcsSource(uri=gcs_source_uri)
    input_config = vision.InputConfig(gcs_source=gcs_source, mime_type=mimetype)

    annotations = []

    logging.info('Beginning PDF annotation.')

    while True:
        next_page = len(annotations) + 1  

        request = vision.AnnotateFileRequest(features=[feature], input_config=input_config, pages=[next_page])
        operation = client.batch_annotate_files(requests=[request])

        annotations.append({ 'page' : next_page, 'text' : operation.responses[0].responses[0].full_text_annotation.text })

        if len(annotations) == operation.responses[0].total_pages:
            break

    logging.info(f'Done annotating {len(annotations)} pages.')

    return annotations

def delete_blob(blob_name, gcp_bucket):
    """Deletes a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(gcp_bucket)
    blob = bucket.blob(blob_name)

    blob.delete()

def detect_text_pdf(input_file, gcp_bucket):
    destination_blob_name = str(uuid.uuid4())

    # Upload the file to GCS
    upload_blob(input_file, destination_blob_name, gcp_bucket)
    
    # Detect text in the document
    gcs_source_uri = f'gs://{gcp_bucket}/{destination_blob_name}'
    annotations = detect_document(gcs_source_uri, MIMETYPE_PDF)

    # Delete the input blob
    delete_blob(destination_blob_name, gcp_bucket)

    return annotations

def detect_text(input_file):
    f = io.open(input_file, 'rb').read()
    image = vision.Image(content=f)

    client = vision.ImageAnnotatorClient()
    ocr = client.text_detection(image=image)

    return [{ 'page' : 1, 'text' : ocr.full_text_annotation.text }]

def main(input_file, output_file, gcp_bucket):
    mimetype = mimetypes.guess_type(input_file)[0]
    if not mimetype:
        logging.error("Unable to identify file's mime type.")
        sys.exit(1)

    # PDF processing goes through a separate process to support multi-page text detection
    if mimetype == MIMETYPE_PDF:
        if not gcp_bucket:
            logging.error("GCP bucket required for PDF processing. Use --gcp-bucket.")
            sys.exit(2)

        result = detect_text_pdf(input_file, gcp_bucket)
    else:
        result = detect_text(input_file)

    json.dump(result, open(output_file, 'w'), indent=2)

    logging.info(f'Text extraction done, results are at {output_file}.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some files.')
    parser.add_argument('--input', type=str, required=True, help='Input file in PDF/JPG/PNG format.')
    parser.add_argument('--output', type=str, required=True, help='Output, in json format.')
    parser.add_argument('--gcp-bucket', type=str, required=False, help='GCP bucket for temporary storage.')

    args = parser.parse_args()
    
    main(args.input, args.output, args.gcp_bucket)

