# AI Assistant Code Modifications for Teams Transcript Processing

## Overview

This document details the specific code modifications required in the AI Assistant to process Microsoft Teams meeting transcripts effectively. Based on analysis of actual Teams transcript samples, we identify the necessary changes to the existing [ai_assistant.py](file:///c:/Users/ABHI%20MANE/Downloads/Aegis_New/Aegis_21-11-2025/backend/routes/ai_assistant.py) file to accommodate the unique structure and characteristics of Teams transcripts.

## Current Code Analysis

The existing [process_transcript()](file:///c:/Users/ABHI%20MANE/Downloads/Aegis_New/Aegis_21-11-2025/backend/routes/ai_assistant.py#L126-L336) function in [ai_assistant.py](file:///c:/Users/ABHI%20MANE/Downloads/Aegis_New/Aegis_21-11-2025/backend/routes/ai_assistant.py) assumes a structured transcript format with explicit metadata sections. The key areas that need modification are:

1. **Format Detection**: Currently no mechanism to distinguish Teams transcripts
2. **Metadata Extraction**: Assumes metadata is in structured sections
3. **Prompt Generation**: Uses generic prompt for all transcript types
4. **Content Preprocessing**: No preprocessing for Teams-specific formats

## Required Modifications

### 1. Format Detection Enhancement

Add format detection logic at the beginning of [process_transcript()](file:///c:/Users/ABHI%20MANE/Downloads/Aegis_New/Aegis_21-11-2025/backend/routes/ai_assistant.py#L126-L336):

```python
def detect_transcript_format(text_content, file_path):
    """
    Detect the format of the transcript based on structural patterns
    Returns: 'structured' or 'teams'
    """
    # Check for Teams transcript patterns
    lines = text_content.split('\n')
    
    # Teams transcripts have speaker lines with timestamp format: "Speaker Name   0:22"
    teams_pattern_count = sum(1 for line in lines if re.match(r'^[^:]+?\s+\d+:\d+$', line.strip()))
    
    # Structured transcripts have explicit metadata sections
    structured_indicators = ['[Meeting Title]:', '[Date]:', '[Attendees]:']
    structured_pattern_count = sum(1 for indicator in structured_indicators if indicator in text_content)
    
    # Also check filename for Teams patterns
    filename = os.path.basename(file_path)
    teams_filename_indicators = ['Meeting Recording', 'Recording', 'Transcript']
    teams_filename_matches = sum(1 for indicator in teams_filename_indicators if indicator in filename)
    
    if teams_pattern_count > 5 or teams_filename_matches > 0:
        return 'teams'
    elif structured_pattern_count > 2:
        return 'structured'
    else:
        return 'unknown'
```

### 2. Teams Transcript Preprocessing

Add preprocessing function for Teams transcripts:

```python
def preprocess_teams_transcript(text_content, file_path):
    """
    Preprocess Teams transcript to extract metadata and clean content
    """
    lines = text_content.split('\n')
    filename = os.path.basename(file_path)
    
    # Extract metadata from filename
    metadata = extract_metadata_from_filename(filename)
    
    # Clean content by removing transcription artifacts
    cleaned_lines = []
    skip_next = False
    
    for i, line in enumerate(lines):
        # Skip transcription start indicator
        if 'started transcription' in line.lower():
            continue
            
        # Skip redundant timestamp lines
        if re.match(r'^\d+:\d+:\d+\s*-->\s*\d+:\d+:\d+$', line.strip()):
            continue
            
        # Extract speakers
        speaker_match = re.match(r'^([^:]+?)\s+(\d+:\d+)$', line.strip())
        if speaker_match:
            speaker = speaker_match.group(1).strip()
            if speaker not in metadata['speakers']:
                metadata['speakers'].append(speaker)
            # Keep the line but clean it
            cleaned_lines.append(f"{speaker}: ")
        else:
            cleaned_lines.append(line)
    
    # Reconstruct content
    cleaned_content = '\n'.join(cleaned_lines)
    
    # Add inferred metadata to content
    header = f"[Meeting Title]: {metadata['title']}\n"
    header += f"[Date]: {metadata['date']}\n"
    header += "[Attendees]:\n"
    for speaker in metadata['speakers']:
        header += f"- {speaker}\n"
    header += "\n" + "="*60 + "\n"
    
    return header + cleaned_content, metadata

def extract_metadata_from_filename(filename):
    """
    Extract metadata from Teams transcript filename
    """
    metadata = {
        'title': 'Untitled Meeting',
        'date': 'Unknown Date',
        'speakers': []
    }
    
    # Extract title (everything before the first hyphen)
    if ' - ' in filename:
        metadata['title'] = filename.split(' - ')[0]
    
    # Extract date from filename (look for date patterns)
    date_patterns = [
        r'(\d{1,2}[^\d]+\d{1,2}[^\d]+\d{4})',  # 27 October 2025
        r'(\d{4}-\d{2}-\d{2})',  # 2025-10-27
        r'(\d{2}-\d{2}-\d{4})'   # 27-10-2025
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, filename)
        if match:
            metadata['date'] = match.group(1)
            break
    
    return metadata
```

### 3. Enhanced Prompt Generation

Modify the prompt generation section to handle different transcript formats:

```python
# After detecting format and preprocessing content
transcript_format = detect_transcript_format(text_content, transcript_path)

if transcript_format == 'teams':
    # Preprocess Teams transcript
    processed_content, metadata = preprocess_teams_transcript(text_content, transcript_path)
    format_instructions = """
IMPORTANT: This is a Microsoft Teams meeting transcript with the following characteristics:
1. Speaker names are followed by timestamps in format "Speaker Name   0:22"
2. Meeting metadata has been inferred from filename and content
3. Some speaker attributions may be incomplete or missing
4. Agenda items are implicit and must be inferred from content flow

Please extract information carefully, noting when metadata was inferred rather than explicitly stated.
"""
else:
    processed_content = text_content
    format_instructions = """
This is a structured meeting transcript with explicit metadata sections.
Extract information as usual from the clearly marked sections.
"""

# Create prompt for LLM
prompt_data = {
    "messages": [
        {
            "role": "system",
            "content": f"You are an AI assistant that converts meeting transcripts into structured Meeting Minutes. Extract key information including title, date, attendees, agenda items, decisions made, action items with assignees, and next meeting details. {format_instructions} Respond ONLY with valid JSON in the following format: {{\"title\": \"Meeting Title\", \"date\": \"YYYY-MM-DD\", \"attendees\":[{{\"name\": \"Attendee Name\", \"role\": \"Attendee Role\"}}], \"agenda\":[\"Agenda Item 1\", \"Agenda Item 2\"], \"decisions\":[\"Decision 1\", \"Decision 2\"], \"action_items\":[{{\"task\": \"Task Description\", \"assignee\": \"Assignee Name\"}}], \"next_meeting\": \"Next meeting details\"}}"
        },
        {
            "role": "user",
            "content": f"Please convert the following meeting transcript into structured Meeting Minutes in JSON format:\n\n{processed_content}\n\nIMPORTANT: Respond ONLY with valid JSON. Do not include any other text, markdown, or explanations."
        }
    ],
    "temperature": 0.3,
    "max_tokens": 2000
}
```

### 4. Enhanced Error Handling

Add specific error handling for Teams transcripts:

```python
# In the JSON parsing section, add format-specific error handling
try:
    mom_data = json.loads(content)
except json.JSONDecodeError:
    # If not JSON, try to extract JSON from markdown code blocks
    import re
    json_match = re.search(r"```(?:json)?\s*({.*?})\s*```", content, re.DOTALL)
    if json_match:
        try:
            mom_data = json.loads(json_match.group(1))
        except json.JSONDecodeError:
            # Create fallback structure with format-specific notes
            mom_data = create_fallback_mom_data(transcript_format)
    else:
        # Create fallback structure with format-specific notes
        mom_data = create_fallback_mom_data(transcript_format)

def create_fallback_mom_data(transcript_format):
    """
    Create fallback Meeting Minutes structure with format-specific notes
    """
    if transcript_format == 'teams':
        notes = "Note: This Meeting Minutes was generated from a Microsoft Teams transcript. Some information may have been inferred due to the unstructured nature of the source format."
    else:
        notes = "Note: Some information could not be extracted from the transcript."
        
    return {
        "title": "Meeting Minutes",
        "date": "N/A",
        "attendees": [],
        "agenda": [notes],
        "decisions": [],
        "action_items": [],
        "next_meeting": "Not specified"
    }
```

## Implementation Steps

### Step 1: Add Required Imports

Add to the imports section at the top of [ai_assistant.py](file:///c:/Users/ABHI%20MANE/Downloads/Aegis_New/Aegis_21-11-2025/backend/routes/ai_assistant.py):

```python
import re
```

### Step 2: Add Helper Functions

Add the helper functions after the imports but before the route definitions:

```python
def detect_transcript_format(text_content, file_path):
    """
    Detect the format of the transcript based on structural patterns
    Returns: 'structured' or 'teams'
    """
    # Check for Teams transcript patterns
    lines = text_content.split('\n')
    
    # Teams transcripts have speaker lines with timestamp format: "Speaker Name   0:22"
    teams_pattern_count = sum(1 for line in lines if re.match(r'^[^:]+?\s+\d+:\d+$', line.strip()))
    
    # Structured transcripts have explicit metadata sections
    structured_indicators = ['[Meeting Title]:', '[Date]:', '[Attendees]:']
    structured_pattern_count = sum(1 for indicator in structured_indicators if indicator in text_content)
    
    # Also check filename for Teams patterns
    filename = os.path.basename(file_path)
    teams_filename_indicators = ['Meeting Recording', 'Recording', 'Transcript']
    teams_filename_matches = sum(1 for indicator in teams_filename_indicators if indicator in filename)
    
    if teams_pattern_count > 5 or teams_filename_matches > 0:
        return 'teams'
    elif structured_pattern_count > 2:
        return 'structured'
    else:
        return 'unknown'

def preprocess_teams_transcript(text_content, file_path):
    """
    Preprocess Teams transcript to extract metadata and clean content
    """
    lines = text_content.split('\n')
    filename = os.path.basename(file_path)
    
    # Extract metadata from filename
    metadata = extract_metadata_from_filename(filename)
    
    # Clean content by removing transcription artifacts
    cleaned_lines = []
    
    for i, line in enumerate(lines):
        # Skip transcription start indicator
        if 'started transcription' in line.lower():
            continue
            
        # Skip redundant timestamp lines
        if re.match(r'^\d+:\d+:\d+\s*-->\s*\d+:\d+:\d+$', line.strip()):
            continue
            
        # Extract speakers
        speaker_match = re.match(r'^([^:]+?)\s+(\d+:\d+)$', line.strip())
        if speaker_match:
            speaker = speaker_match.group(1).strip()
            if speaker not in metadata['speakers']:
                metadata['speakers'].append(speaker)
            # Keep the line but clean it
            cleaned_lines.append(f"{speaker}: ")
        else:
            cleaned_lines.append(line)
    
    # Reconstruct content
    cleaned_content = '\n'.join(cleaned_lines)
    
    # Add inferred metadata to content
    header = f"[Meeting Title]: {metadata['title']}\n"
    header += f"[Date]: {metadata['date']}\n"
    header += "[Attendees]:\n"
    for speaker in metadata['speakers']:
        header += f"- {speaker}\n"
    header += "\n" + "="*60 + "\n"
    
    return header + cleaned_content, metadata

def extract_metadata_from_filename(filename):
    """
    Extract metadata from Teams transcript filename
    """
    metadata = {
        'title': 'Untitled Meeting',
        'date': 'Unknown Date',
        'speakers': []
    }
    
    # Extract title (everything before the first hyphen)
    if ' - ' in filename:
        metadata['title'] = filename.split(' - ')[0]
    
    # Extract date from filename (look for date patterns)
    date_patterns = [
        r'(\d{1,2}[^\d]+\d{1,2}[^\d]+\d{4})',  # 27 October 2025
        r'(\d{4}-\d{2}-\d{2})',  # 2025-10-27
        r'(\d{2}-\d{2}-\d{4})'   # 27-10-2025
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, filename)
        if match:
            metadata['date'] = match.group(1)
            break
    
    return metadata

def create_fallback_mom_data(transcript_format):
    """
    Create fallback Meeting Minutes structure with format-specific notes
    """
    if transcript_format == 'teams':
        notes = "Note: This Meeting Minutes was generated from a Microsoft Teams transcript. Some information may have been inferred due to the unstructured nature of the source format."
    else:
        notes = "Note: Some information could not be extracted from the transcript."
        
    return {
        "title": "Meeting Minutes",
        "date": "N/A",
        "attendees": [],
        "agenda": [notes],
        "decisions": [],
        "action_items": [],
        "next_meeting": "Not specified"
    }
```

### Step 3: Modify the [process_transcript()](file:///c:/Users/ABHI%20MANE/Downloads/Aegis_New/Aegis_21-11-2025/backend/routes/ai_assistant.py#L126-L336) Function

Replace the content extraction and prompt generation section (lines 127-149) with:

```python
def process_transcript():
    # Extract text from transcript
    if transcript_path.endswith('.docx'):
        doc = DocxDocument(transcript_path)
        text_content = "\n".join([para.text for para in doc.paragraphs])
    else:  # .txt file
        with open(transcript_path, "r", encoding="utf-8") as f:
            text_content = f.read()
    
    # Detect transcript format
    transcript_format = detect_transcript_format(text_content, transcript_path)
    
    # Process based on format
    if transcript_format == 'teams':
        # Preprocess Teams transcript
        processed_content, metadata = preprocess_teams_transcript(text_content, transcript_path)
        format_instructions = """
IMPORTANT: This is a Microsoft Teams meeting transcript with the following characteristics:
1. Speaker names are followed by timestamps in format "Speaker Name   0:22"
2. Meeting metadata has been inferred from filename and content
3. Some speaker attributions may be incomplete or missing
4. Agenda items are implicit and must be inferred from content flow

Please extract information carefully, noting when metadata was inferred rather than explicitly stated.
"""
    else:
        processed_content = text_content
        format_instructions = """
This is a structured meeting transcript with explicit metadata sections.
Extract information as usual from the clearly marked sections.
"""
    
    # Create prompt for LLM
    prompt_data = {
        "messages": [
            {
                "role": "system",
                "content": f"You are an AI assistant that converts meeting transcripts into structured Meeting Minutes. Extract key information including title, date, attendees, agenda items, decisions made, action items with assignees, and next meeting details. {format_instructions} Respond ONLY with valid JSON in the following format: {{\"title\": \"Meeting Title\", \"date\": \"YYYY-MM-DD\", \"attendees\":[{{\"name\": \"Attendee Name\", \"role\": \"Attendee Role\"}}], \"agenda\":[\"Agenda Item 1\", \"Agenda Item 2\"], \"decisions\":[\"Decision 1\", \"Decision 2\"], \"action_items\":[{{\"task\": \"Task Description\", \"assignee\": \"Assignee Name\"}}], \"next_meeting\": \"Next meeting details\"}}"
            },
            {
                "role": "user",
                "content": f"Please convert the following meeting transcript into structured Meeting Minutes in JSON format:\n\n{processed_content}\n\nIMPORTANT: Respond ONLY with valid JSON. Do not include any other text, markdown, or explanations."
            }
        ],
        "temperature": 0.3,
        "max_tokens": 2000
    }
    
    # Rest of the function remains the same...
```

### Step 4: Update Error Handling

Replace the JSON parsing error handling section (lines 232-275) with:

```python
# Extract content from response
if "choices" in llm_response and len(llm_response["choices"]) > 0:
    content = llm_response["choices"][0]["message"]["content"]
    
    # Try to parse as JSON
    try:
        mom_data = json.loads(content)
    except json.JSONDecodeError:
        # If not JSON, try to extract JSON from markdown code blocks
        import re
        json_match = re.search(r"```(?:json)?\s*({.*?})\s*```", content, re.DOTALL)
        if json_match:
            try:
                mom_data = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                # If still not valid JSON, create a fallback structure
                mom_data = create_fallback_mom_data(transcript_format)
                # Try to extract some basic information from the content
                if content:
                    # Extract title from first line if possible
                    lines = content.strip().split('\n')
                    if lines and lines[0].strip():
                        mom_data["title"] = lines[0].strip()[:100]  # Limit title length
        else:
            # Create fallback structure if no JSON found
            mom_data = create_fallback_mom_data(transcript_format)
            # Try to extract some basic information from the content
            if content:
                # Extract title from first line if possible
                lines = content.strip().split('\n')
                if lines and lines[0].strip():
                    mom_data["title"] = lines[0].strip()[:100]  # Limit title length
else:
    raise Exception("Invalid LLM response format")
```

## Testing Considerations

### Test Cases to Validate

1. **Format Detection Accuracy**
   - Verify correct identification of Teams vs. structured transcripts
   - Test with edge cases and mixed format content

2. **Metadata Extraction**
   - Validate title extraction from various filename patterns
   - Confirm date parsing from different formats
   - Check speaker identification accuracy

3. **Content Processing**
   - Ensure dialogue cleaning removes artifacts without losing content
   - Verify agenda item identification from content flow
   - Test decision and action item extraction

4. **Output Quality**
   - Compare Meeting Minutes quality between formats
   - Validate JSON structure compliance
   - Check fallback mechanism effectiveness

## Performance Considerations

1. **Memory Usage**: Teams transcripts can be large; implement efficient processing
2. **Processing Time**: Optimize regex operations and content parsing
3. **Scalability**: Design for handling multiple concurrent transcript processing requests

## Backward Compatibility

The modifications maintain full backward compatibility with existing structured transcript formats by:
1. Preserving existing processing logic for structured transcripts
2. Maintaining identical output JSON structure
3. Keeping all existing API endpoints unchanged
4. Ensuring no breaking changes to current functionality

This implementation will enable the AI Assistant to process Microsoft Teams meeting transcripts while maintaining the high quality and reliability of Meeting Minutes generation that users expect.