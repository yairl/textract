# Overview

Simple code for performing text extraction using Google Cloud Vision API.
Supported formats: GIF, JPEG, PDF, PNG, TIFF.

Output generated as JSON file, loadable via json.load.

# How to run
env GOOGLE_APPLICATION_CREDENTIALS=<your credentials here> ./textract.py --input <> --output <>.json
