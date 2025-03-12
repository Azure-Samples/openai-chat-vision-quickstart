# Define the .env file path
$envFilePath = ".env"

# Clear the contents of the .env file
Set-Content -Path $envFilePath -Value ""

# Append new values to the .env file
$azureOpenAiEndpoint = azd env get-value AZURE_OPENAI_ENDPOINT
$azureOpenAiDeployment = azd env get-value AZURE_OPENAI_DEPLOYMENT
$azureOpenAiApiVersion = azd env get-value AZURE_OPENAI_API_VERSION
$azureTenantId = azd env get-value AZURE_TENANT_ID

Add-Content -Path $envFilePath -Value "OPENAI_HOST=azure"
Add-Content -Path $envFilePath -Value "OPENAI_MODEL=$azureOpenAiDeployment"
Add-Content -Path $envFilePath -Value ""
Add-Content -Path $envFilePath -Value "AZURE_OPENAI_ENDPOINT=$azureOpenAiEndpoint"
Add-Content -Path $envFilePath -Value "AZURE_OPENAI_API_VERSION=$azureOpenAiApiVersion"
Add-Content -Path $envFilePath -Value "AZURE_TENANT_ID=$azureTenantId"
Add-Content -Path $envFilePath -Value ""
