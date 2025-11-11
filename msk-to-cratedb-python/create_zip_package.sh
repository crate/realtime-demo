#!/bin/bash

# This script generates a deployable ZIP archive.
# https://docs.aws.amazon.com/lambda/latest/dg/python-package.html

# Clean up previous build artifacts
rm -rf package lambda.zip
mkdir package

# Install dependencies from requirements.txt into the package directory
pip3 install --target package -r src/requirements.txt

# Create a ZIP archive
cd package
zip -r ../lambda.zip .

# Add the actual Lambda function code. -j skips the src part of the path.
cd ..
zip -j lambda.zip src/lambda_function.py

echo "Lambda ZIP file successfully created as lambda.zip"
