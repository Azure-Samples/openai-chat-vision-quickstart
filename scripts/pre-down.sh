#!/bin/bash

az cognitiveservices account deployment delete --name $AZURE_OPENAI_RESOURCE_NAME --resource-group $AZURE_RESOURCE_GROUP --deployment-name $AZURE_OPENAI_CHATGPT_DEPLOYMENT
