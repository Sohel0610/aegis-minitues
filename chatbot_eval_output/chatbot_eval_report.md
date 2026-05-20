# AEGIS Chatbot Database Evaluation Report

Generated on: 2026-05-20 02:46:51
SQLite database used: `E:\Abhishek\final-prod\aegis-platform\sqlite.db`

## Executive Summary

This test pack validates whether the current chatbot can answer database-grounded regulatory questions before RAG/vector search is introduced.
The questions are generated directly from the latest SQLite export and cover BSE, SEBI, and RBI data equally.

## Question Coverage

Total questions generated: **900**

- BSE: 300 questions
- SEBI: 300 questions
- RBI: 300 questions

## Test Categories

- Bar Chart Comparison: 18
- Chart by Topic: 46
- Distribution: 17
- Entity Count: 18
- Executive Summary: 64
- Filter Request: 17
- Latest Update: 49
- Manager Brief: 64
- Month Comparison: 8
- Persona - Board Member: 30
- Persona - Business User: 30
- Persona - CEO: 30
- Persona - CFO: 30
- Persona - CTO: 30
- Persona - Compliance Officer: 30
- Persona - Investor Relations: 30
- Persona - Legal Head: 30
- Persona - Operations Head: 30
- Persona - Risk Manager: 30
- Question Answering: 23
- Risk/Compliance Lens: 47
- Source Evidence: 58
- Table Request: 60
- Top N Ranking: 17
- Topic Search: 64
- Total Count: 2
- Trend Chart: 28

## Chatbot Run Results

Questions sent to chatbot: **900**
Automatic pass: **218**
Needs manual check: **441**
API errors: **241**
Indicative pass rate: **24.22%**
Average response time: **400.44 ms**

Note: PASS/CHECK is keyword-based, not an LLM judge. CHECK does not always mean wrong; it means a human should review the answer.

## Output Files

- `chatbot_eval_questions.csv`: all 900 questions with expected evidence
- `chatbot_eval_questions.json`: machine-readable question set
- `chatbot_eval_answers.csv`: chatbot answers and automatic review status, created only when `--run` is used
- `chatbot_eval_report.md`: this manager-friendly report

## Manager Notes

This evaluation is suitable for pre-RAG validation because it tests direct database retrieval and routing behavior.
After vector database access is available, add semantic/paraphrase-heavy questions and compare RAG answers against this baseline.