# PowerShell script for Azure LLM API calls
# Usage: .\llm_client.ps1 prompt.json

param(
    [Parameter(Mandatory=$true)]
    [string]$PromptFile
)

# Get environment variables
$DEPLOYMENT = $env:LLM_DEPLOYMENT
$ENDPOINT = $env:LLM_ENDPOINT
$KEY = $env:LLM_API_KEY

# Validate inputs
if (-not $DEPLOYMENT) {
    Write-Error "LLM_DEPLOYMENT environment variable not set"
    exit 1
}

if (-not $ENDPOINT) {
    Write-Error "LLM_ENDPOINT environment variable not set"
    exit 1
}

if (-not $KEY) {
    Write-Error "LLM_API_KEY environment variable not set"
    exit 1
}

if (-not (Test-Path $PromptFile)) {
    Write-Error "Prompt file not found: $PromptFile"
    exit 1
}

# Read the prompt file
$PromptContent = Get-Content -Path $PromptFile -Raw

# Make the API call
$Headers = @{
    "Content-Type" = "application/json"
    "api-key" = $KEY
}

$Uri = "$ENDPOINT/openai/deployments/$DEPLOYMENT/chat/completions?api-version=2023-05-15"

try {
    $Response = Invoke-RestMethod -Uri $Uri -Method Post -Headers $Headers -Body $PromptContent -SkipCertificateCheck
    $Response | ConvertTo-Json -Depth 10
} catch {
    Write-Error "API call failed: $($_.Exception.Message)"
    exit 1
}