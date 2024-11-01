#!/bin/bash

# Define the .env file path
ENV_FILE_PATH=".env"

# Clear the contents of the .env file
> $ENV_FILE_PATH

echo "OPENAI_HOST=azure" >> $ENV_FILE_PATH
echo "OPENAI_MODEL=$(azd env get-value AZURE_OPENAI_DEPLOYMENT)" >> $ENV_FILE_PATH
echo "" >> $ENV_FILE_PATH
echo "AZURE_OPENAI_ENDPOINT=$(azd env get-value AZURE_OPENAI_ENDPOINT)" >> $ENV_FILE_PATH
echo "AZURE_OPENAI_API_VERSION=$(azd env get-value AZURE_OPENAI_API_VERSION)" >> $ENV_FILE_PATH
echo "AZURE_TENANT_ID=$(azd env get-value AZURE_TENANT_ID)" >> $ENV_FILE_PATH
echo "" >> $ENV_FILE_PATH
echo "GITHUB_MODELS_ENDPOINT=https://models.inference.ai.azure.com" >> $ENV_FILE_PATH
