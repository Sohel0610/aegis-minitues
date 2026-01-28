# Microsoft Teams Transcript Processing - Requirements, Solution, Approach (RSA)

## 1. Requirements Analysis

### 1.1 Functional Requirements

**FR-01: Format Compatibility**
- The AI assistant must process Microsoft Teams meeting transcripts (.docx format)
- The system must maintain compatibility with existing structured transcript formats
- Output quality must be equivalent regardless of input format

**FR-02: Metadata Extraction**
- Extract meeting title from filename (e.g., "AGE23L - Board Meeting - 3.00 p.m. IST, Monday, 27th October, 2025")
- Identify meeting date from filename or content references
- Recognize attendee names from speaker labels in dialogue (e.g., "Dinesh Kanabar", "Anup Shah", "Romesh Sobti")
- Infer meeting purpose and context from content analysis

**FR-03: Content Processing**
- Parse timestamped dialogue segments accurately (e.g., "Dinesh Kanabar   0:22")
- Resolve speaker attribution inconsistencies and variations in naming
- Identify agenda items, decisions, and action items from unstructured dialogue
- Generate structured Meeting Minutes in JSON format

**FR-04: Error Handling**
- Gracefully handle missing or incomplete metadata
- Provide fallback mechanisms for speaker attribution failures
- Validate extracted information for consistency and plausibility

### 1.2 Non-Functional Requirements

**NFR-01: Performance**
- Processing time should not exceed 30 seconds for typical meeting transcripts
- Memory usage should remain within reasonable limits for large transcripts

**NFR-02: Reliability**
- System should handle 95% of Teams transcript variations successfully
- Error recovery mechanisms should prevent complete processing failures

**NFR-03: Maintainability**
- Modular design to accommodate future transcript format changes
- Clear separation between format detection, preprocessing, and content analysis

## 2. Solution Design

### 2.1 Architecture Overview

The solution involves enhancing the existing AI assistant pipeline with format-aware processing capabilities:

```
Input Transcript
      ↓
Format Detection Module
      ↓
Preprocessing Pipeline
      ↓
Content Analysis & Metadata Extraction
      ↓
LLM-Based Meeting Minutes Generation
      ↓
Structured Output (JSON/DOCX)
```

### 2.2 Core Components

#### 2.2.1 Format Detection Module
- Analyzes input file characteristics
- Identifies Teams transcript vs. structured format
- Routes to appropriate processing pipeline

#### 2.2.2 Teams Transcript Preprocessor
- Cleans timestamp information
- Normalizes speaker attribution
- Extracts metadata from filename and content patterns
- Structures content for LLM processing

#### 2.2.3 Enhanced Prompt Engine
- Dynamically generates prompts based on input format
- Provides format-specific examples and instructions
- Adjusts LLM expectations for metadata availability

#### 2.2.4 Metadata Inference Engine
- Applies NLP techniques to extract meeting information
- Uses contextual clues for date, title, and attendee identification
- Implements confidence scoring for extracted elements

### 2.3 Data Flow

1. **Input Reception**: Transcript file uploaded via existing endpoint
2. **Format Analysis**: System determines transcript type
3. **Preprocessing**: Teams transcripts undergo specialized cleaning
4. **Metadata Extraction**: Key meeting information inferred from content
5. **Prompt Generation**: Custom prompt created based on format and extracted metadata
6. **LLM Processing**: Enhanced prompt sent to language model
7. **Output Generation**: Structured Meeting Minutes produced in JSON format
8. **Document Creation**: MoM converted to DOCX format

## 3. Implementation Approach

### 3.1 Phase 1: Foundation (Week 1-2)

#### 3.1.1 Format Detection Enhancement
- Extend the [process_transcript()](file:///c:/Users/ABHI%20MANE/Downloads/Aegis_New/Aegis_21-11-2025/backend/routes/ai_assistant.py#L126-L336) function in [ai_assistant.py](file:///c:/Users/ABHI%20MANE/Downloads/Aegis_New/Aegis_21-11-2025/backend/routes/ai_assistant.py) to detect Teams transcript characteristics
- Implement pattern matching for timestamp formats (e.g., "Name   0:22")
- Create format classification logic based on structural patterns

#### 3.1.2 Teams Transcript Preprocessor
- Develop preprocessing logic to clean Teams transcript format
- Remove redundant lines and normalize speaker identification
- Extract meeting title from filename patterns
- Parse date information from filename or content

### 3.2 Phase 2: Enhanced Processing (Week 2-3)

#### 3.2.1 Metadata Inference Engine
- Implement algorithms to extract attendees from speaker labels
- Develop date parsing logic from various formats
- Create meeting title inference from filename and content context

#### 3.2.2 Prompt Engineering
- Modify system prompt to handle unstructured transcript formats
- Provide examples of Teams transcript processing
- Adjust LLM expectations for metadata availability

### 3.3 Phase 3: Integration & Testing (Week 3-4)

#### 3.3.1 Pipeline Integration
- Integrate format detection with existing processing pipeline
- Ensure backward compatibility with structured transcripts
- Implement error handling and fallback mechanisms

#### 3.3.2 Testing & Validation
- Test with provided Teams transcript samples
- Validate Meeting Minutes quality and accuracy
- Optimize processing performance

## 4. Detailed Technical Implementation

### 4.1 Format Detection Logic

Teams transcripts can be identified by these characteristics:
1. Speaker lines with timestamp format: "Speaker Name   0:22"
2. Filename patterns containing meeting information
3. Absence of structured metadata sections ([Meeting Title], [Date], etc.)

### 4.2 Preprocessing Steps

1. **Content Cleaning**:
   - Remove redundant lines (e.g., "Pragnesh Darji started transcription")
   - Normalize speaker identification format
   - Clean up timestamp information

2. **Metadata Extraction**:
   - Parse filename to extract meeting title and date
   - Identify speakers from dialogue segments
   - Extract meeting context from opening statements

### 4.3 Enhanced Prompt Structure

The system prompt needs to be modified to instruct the LLM on:
1. How to handle unstructured transcript formats
2. What to do when metadata is not explicitly provided
3. How to identify agenda items, decisions, and action items from dialogue flow

### 4.4 Error Handling

1. **Fallback Mechanisms**:
   - When meeting title cannot be extracted, use filename as fallback
   - When date is unclear, indicate as "N/A" rather than failing
   - When speaker roles are not explicit, list attendees without roles

2. **Validation**:
   - Cross-check extracted information for consistency
   - Implement confidence scoring for key elements
   - Provide quality indicators in the output

## 5. Expected Outcomes

### 5.1 Immediate Benefits
- Support for Microsoft Teams meeting transcripts
- Maintained compatibility with existing structured formats
- Consistent Meeting Minutes quality across formats

### 5.2 Long-term Advantages
- Flexible architecture for future transcript format support
- Enhanced metadata inference capabilities
- Improved natural language processing for unstructured content

## 6. Risk Mitigation

### 6.1 Technical Risks
- **Inconsistent Speaker Attribution**: Implement fuzzy matching for speaker names
- **Missing Metadata**: Provide robust fallback mechanisms
- **Performance Issues**: Optimize preprocessing algorithms

### 6.2 Quality Risks
- **Reduced Accuracy**: Implement validation and confidence scoring
- **Incomplete Information Extraction**: Provide clear indicators of missing information
- **Format Variations**: Design flexible parsing logic

## 7. Success Metrics

1. **Processing Success Rate**: ≥95% of Teams transcripts processed successfully
2. **Output Quality**: Equivalent to structured transcript processing
3. **Performance**: ≤30 seconds processing time for typical transcripts
4. **Compatibility**: 100% backward compatibility with existing formats

This RSA document provides a comprehensive framework for adapting the AI assistant to process Microsoft Teams meeting transcripts while maintaining the quality and reliability of Meeting Minutes generation.