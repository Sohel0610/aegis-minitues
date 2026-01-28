#!/bin/bash
# Usage: ./llm_client.sh prompt.json

PROMPT_FILE=$1
DEPLOYMENT=${LLM_DEPLOYMENT}
ENDPOINT=${LLM_ENDPOINT}
KEY=${LLM_API_KEY}

curl -s -k -X POST "$ENDPOINT/openai/deployments/$DEPLOYMENT/chat/completions?api-version=2023-05-15" \
  -H "Content-Type: application/json" \
  -H "api-key: $KEY" \
  -d @"$PROMPT_FILE"