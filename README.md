# Overview

Performs OCR-based text extraction using Google Cloud Vision API.
Supported formats: GIF, JPEG, PDF, PNG, TIFF.

Output generated as JSON file, loadable via json.load.

# Requirements

pip3 install requirements.pip

# How to run

env GOOGLE_APPLICATION_CREDENTIALS=<your credentials here> ./textract.py --input <> --output <>.json
