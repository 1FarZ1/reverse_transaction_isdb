# AAOIFI FAS Analyzer (Agentic AI Version)

## Introduction

The **AAOIFI FAS Analyzer** is an interactive, AI-powered Streamlit application built to assist finance professionals, auditors, and students in analyzing Islamic finance journal entries for compliance with AAOIFI Financial Accounting Standards (FAS). The app leverages OpenAI's GPT-4 model (via LangChain) to parse journal entries, identify the most relevant FAS standards, and check for Sharia compliance. It provides detailed explanations, highlights matched keywords, and references the applicable Sharia standards, making it a valuable tool for Islamic finance accounting and compliance.

## How to Run the App

### 1. Prerequisites

- Python 3.9 or higher
- An OpenAI API key with access to GPT-4

### 2. Installation

Clone the repository and install dependencies:

```bash
git clone <your-repo-url>
cd <your-repo-folder>
pip install -r requirements.txt
```

Your `requirements.txt` should include:
```
streamlit
openai
langchain
langchain-openai
```

### 3. Set Your OpenAI API Key

Set your API key as an environment variable (recommended):

```bash
export OPENAI_API_KEY=sk-...
```

Or update the code to read from `st.secrets` or environment variables instead of hardcoding.

### 4. Run the App

```bash
streamlit run main.py
```

### 5. Usage

- Select or enter a journal entry in the "Analyze Entry" tab.
- Click **Analyze**.
- Review the parsed journal entry, FAS matches, explanations, and Sharia compliance results.
- Explore FAS standards in the "View FAS Standards" tab.

## Architecture

### Component Overview

| Component           | Description                                                                                 |
|---------------------|--------------------------------------------------------------------------------------------|
| Streamlit UI        | User interface for data input, results display, and navigation.                            |
| AAOIFIAgent Class   | Encapsulates LLM, tools, memory, and agent logic. Handles parsing and analysis workflows.  |
| LangChain Agent     | Orchestrates LLM reasoning, tool use, and memory for multi-step analysis.                  |
| Tools               | - **FASLookupTool**: Retrieves FAS standard details.<br>- **ShariaComplianceTool**: Checks compliance. |
| Prompt Template     | Guides the LLM in extracting context, accounts, and linking to FAS standards.              |
| Memory              | ConversationBufferMemory preserves chat context across interactions.                       |

### Data Flow

1. **User Input**: Journal entry is provided via the Streamlit UI.
2. **Parsing**: The entry is parsed to extract debits, credits, context, and adjustments.
3. **Agent Analysis**: The agent (using GPT-4 via LangChain) analyzes the entry, invokes tools, and generates structured results.
4. **Results Display**: Streamlit presents parsed data, FAS matches (with confidence, explanation, matched keywords), and Sharia compliance status.

### Key Technologies

- **Streamlit**: For rapid web UI development and interactive visualization.
- **LangChain**: For agent orchestration, tool integration, and prompt management.
- **OpenAI GPT-4**: For advanced natural language understanding and reasoning.
- **Custom Tools**: For standard lookup and compliance checking.

## Specification

- **Input**: Freeform journal entry text (optionally with context and adjustments).
- **Output**:
    - Parsed debits, credits, context, and adjustments.
    - Ranked list of relevant FAS standards with confidence scores, explanations, and matched keywords.
    - Sharia compliance status with references and issues (if any).
- **Extensible**: Easily add new tools, standards, or compliance checks.
- **Memory**: Maintains conversational context for multi-turn analysis.
- **Security**: API keys should be managed securely (not hardcoded in production).

## Example Workflow

1. **User** selects a sample or enters a custom journal entry.
2. **App** parses the entry and displays structured information.
3. **Agent** analyzes the entry, identifies relevant FAS standards, and checks compliance.
4. **Results** are presented in an organized, visually appealing format with explanations and references.

## Notes

- The current implementation uses a mock analysis in `analyze_entry`. To enable dynamic, LLM-powered analysis, update `analyze_entry` to invoke the agent as described in the code comments.
- All FAS standards and example entries are included in the app for reference and testing.

This app serves as a foundation for building advanced Islamic finance compliance tools, enabling transparent, explainable, and interactive accounting analysis.
