@echo off
setlocal

REM Usage: llm_client.bat prompt.json

set PROMPT_FILE=%1
set DEPLOYMENT=%LLM_DEPLOYMENT%
set ENDPOINT=%LLM_ENDPOINT%
set KEY=%LLM_API_KEY%

curl -s -X POST "%ENDPOINT%/openai/deployments/%DEPLOYMENT%/chat/completions?api-version=2023-05-15" ^
  -H "Content-Type: application/json" ^
  -H "api-key: %KEY%" ^
  -d @%PROMPT_FILE%