@echo off
setlocal

REM Usage: llm_client.bat prompt.json
set PROMPT_FILE=%~1
set DEPLOYMENT=%LLM_DEPLOYMENT%
set ENDPOINT=%LLM_ENDPOINT%
set KEY=%LLM_API_KEY%
set USE_GROQ=%USE_GROQ%
set GROQ_MODEL=%GROQ_MODEL%
set GROQ_ENDPOINT=%GROQ_ENDPOINT%

REM Set default values if not provided
if "%USE_GROQ%"=="" set USE_GROQ=false
if "%GROQ_MODEL%"=="" set GROQ_MODEL=llama3-8b-8192
if "%GROQ_ENDPOINT%"=="" set GROQ_ENDPOINT=https://api.groq.com/openai/v1

REM Validate input
if "%PROMPT_FILE%"=="" (
    echo Error: Prompt file not provided
    echo Usage: llm_client.bat prompt.json
    exit /b 1
)

if not exist "%PROMPT_FILE%" (
    echo Error: Prompt file not found: %PROMPT_FILE%
    exit /b 1
)

REM Make API call
if "%USE_GROQ%"=="true" (
    REM Use Groq API
    curl -s -X POST "%GROQ_ENDPOINT%/chat/completions" ^
      -H "Content-Type: application/json" ^
      -H "Authorization: Bearer %KEY%" ^
      -d @"%PROMPT_FILE%"
) else (
    REM Use Azure OpenAI API
    curl -s -X POST "%ENDPOINT%/openai/deployments/%DEPLOYMENT%/chat/completions?api-version=2023-05-15" ^
      -H "Content-Type: application/json" ^
      -H "api-key: %KEY%" ^
      -d @"%PROMPT_FILE%"
)