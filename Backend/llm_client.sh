#!/bin/bash

# Usage: ./llm_client.sh prompt.json
PROMPT_FILE=$1
DEPLOYMENT=${LLM_DEPLOYMENT:-"az10gpt41mdmrctbtp01"}
ENDPOINT=${LLM_ENDPOINT:-"https://az10oaidmrctbtp01.openai.azure.com"}
KEY=${LLM_API_KEY:-"a026dffd6de4451f8986fe1a6e1a1649"}
USE_GROQ=${USE_GROQ:-"false"}
GROQ_MODEL=${GROQ_MODEL:-"llama3-8b-8192"}
GROQ_ENDPOINT=${GROQ_ENDPOINT:-"https://api.groq.com/openai/v1"}

# Validate input
if [ -z "$PROMPT_FILE" ]; then
    echo "Error: Prompt file not provided"
    echo "Usage: ./llm_client.sh prompt.json"
    exit 1
fi

if [ ! -f "$PROMPT_FILE" ]; then
    echo "Error: Prompt file not found: $PROMPT_FILE"
    exit 1
fi

# Make API call
if [ "$USE_GROQ" = "false" ]; then
    # Use Groq API
    curl -s -X POST "$GROQ_ENDPOINT/chat/completions" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $KEY" \
      -d @"$PROMPT_FILE"
else
    # Use Azure OpenAI API
    curl -s -X POST "$ENDPOINT/openai/deployments/$DEPLOYMENT/chat/completions?api-version=2023-05-15" \
      -H "Content-Type: application/json" \
      -H "api-key: $KEY" \
      -d @"$PROMPT_FILE"
fi