# Text to Process Model - System Design

Complete system architecture, workflows, and technical design for the BPMN generation platform.

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Data Flow](#data-flow)
4. [Component Design](#component-design)
5. [API Design](#api-design)
6. [Database Schema](#database-schema)
7. [Deployment Architecture](#deployment-architecture)
8. [Security Design](#security-design)

---

## System Overview

```mermaid
graph TB
    User["👤 User"]
    CLI["CLI Interface"]
    API["REST API"]
    OrchestratorAgent["🤖 Orchestrator Agent"]
    Parser["📝 Parser Agent"]
    Modeler["📐 Modeler Agent"]
    LLM["🧠 Mistral LLM"]
    FileSystem["💾 File System"]
    Output["📁 Output Files"]

    User -->|Interactive| CLI
    User -->|HTTP Request| API
    CLI --> OrchestratorAgent
    API --> OrchestratorAgent
    OrchestratorAgent -->|Orchestrates| Parser
    OrchestratorAgent -->|Orchestrates| Modeler
    Parser -->|Queries| LLM
    Modeler -->|Queries| LLM
    Parser --> FileSystem
    Modeler --> FileSystem
    FileSystem --> Output
```

---

## Architecture

### High-Level Architecture

```mermaid
graph LR
    subgraph "Input Layer"
        CLI["CLI Interface"]
        API["REST API"]
        File["File Input"]
    end

    subgraph "Processing Layer"
        OrchestratorAgent["Orchestrator Agent"]
        ParserAgent["Parser Agent"]
        ModelerAgent["Modeler Agent"]
    end

    subgraph "LLM Layer"
        MistralAPI["Mistral API<br/>Large Language Model"]
    end

    subgraph "Storage Layer"
        FileSystem["Local File System"]
        OutputDir["Output Directory"]
    end

    CLI --> OrchestratorAgent
    API --> OrchestratorAgent
    File --> OrchestratorAgent
    OrchestratorAgent --> ParserAgent
    OrchestratorAgent --> ModelerAgent
    ParserAgent --> MistralAPI
    ModelerAgent --> MistralAPI
    ParserAgent --> FileSystem
    ModelerAgent --> FileSystem
    FileSystem --> OutputDir
```

### Component Interaction Diagram

```mermaid
graph TD
    A["User Input<br/>Natural Language<br/>Process Description"]
    
    A --> B["OrchestratorAgent<br/>"]
    
    B -->|Step 1| C["ParserAgent"]
    C -->|Analyzes| D["Mistral LLM<br/>Parser Prompt"]
    D -->|Returns| E["Structured Elements<br/>+ Pseudocode"]
    
    E -->|Saves| F["Parser Output<br/>output/parser/"]
    
    E -->|Step 2| G["ModelerAgent"]
    G -->|Generates| H["Mistral LLM<br/>Modeler Prompt"]
    H -->|Returns| I["BPMN 2.0 JSON<br/>+ Explanation"]
    
    I -->|Saves| J["Modeler Output<br/>output/modeler/"]
    
    F --> K["Final Results<br/>Complete Workflow"]
    J --> K
```

---

## Data Flow

### End-to-End Process Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI/API
    participant OrchestratorAgent
    participant Parser
    participant Mistral
    participant FileSystem
    participant Output

    User->>CLI/API: Submit process description
    CLI/API->>OrchestratorAgent: Initialize workflow
    
    rect rgb(200, 220, 255)
        Note over Parser,Mistral: PARSING PHASE
        OrchestratorAgent->>Parser: parse(description)
        Parser->>Mistral: Query with parser prompt
        Mistral-->>Parser: Elements + Pseudocode
        Parser->>FileSystem: Save elements.txt
        Parser->>FileSystem: Save pseudocode.txt
        Parser->>FileSystem: Save metadata.json
    end
    
    rect rgb(220, 255, 200)
        Note over OrchestratorAgent,Mistral: MODELING PHASE
        OrchestratorAgent->>Mistral: Get parsed output
        OrchestratorAgent->>Modeler: generate_model(pseudocode)
        Modeler->>Mistral: Query with modeler prompt
        Mistral-->>Modeler: BPMN JSON + Explanation
        Modeler->>FileSystem: Save bpmn_model.json
        Modeler->>FileSystem: Save explanation.txt
        Modeler->>FileSystem: Save metadata.json
    end
    
    FileSystem->>Output: Organize by process_name
    Output-->>CLI/API: Return results
    CLI/API-->>User: Display summary + file paths
```

### REST API Request/Response Flow

```mermaid
sequenceDiagram
    participant Client
    participant API Server
    participant OrchestratorAgent
    participant LLM Service
    participant Storage

    Client->>API Server: POST /transform<br/>{description, name}
    
    API Server->>OrchestratorAgent: run_complete_workflow()
    
    OrchestratorAgent->>LLM Service: Parser phase
    LLM Service-->>OrchestratorAgent: Elements
    
    OrchestratorAgent->>Storage: Save parser results
    Storage-->>OrchestratorAgent: Saved paths
    
    OrchestratorAgent->>LLM Service: Modeler phase
    LLM Service-->>OrchestratorAgent: BPMN model
    
    OrchestratorAgent->>Storage: Save modeler results
    Storage-->>OrchestratorAgent: Saved paths
    
    OrchestratorAgent-->>API Server: Complete workflow result
    
    API Server->>Client: 200 OK<br/>{status, files, paths}
    
    Client->>API Server: GET /download/{name}/bpmn_model
    Storage->>API Server: File content
    API Server-->>Client: File download
```

---

## Component Design

### Parser Agent

```mermaid
graph TD
    A["Process Description"] --> B["ParserAgent"]
    
    B --> C["Load System Prompt"]
    C --> D["parser_prompt.md"]
    
    B --> E["Initialize Mistral LLM"]
    E --> F["ChatMistralAI<br/>model=mistral-large"]
    
    B --> G["Parse Description"]
    G --> H["Extract Elements<br/>Tasks, Events, Gateways"]
    
    H --> I["Generate Pseudocode"]
    
    I --> J["Save Results"]
    J --> K["elements.txt"]
    J --> L["pseudocode.txt"]
    J --> M["full_response.txt"]
    J --> N["metadata.json"]
    
    K --> O["output/parser/{name}/"]
    L --> O
    M --> O
    N --> O
```

### Modeler Agent

```mermaid
graph TD
    A["Parsed Pseudocode"] --> B["ModelerAgent"]
    
    B --> C["Load System Prompt"]
    C --> D["modeler_prompt.md"]
    
    B --> E["Initialize Mistral LLM"]
    E --> F["ChatMistralAI<br/>model=mistral-large"]
    
    B --> G["Generate BPMN Model"]
    G --> H["Extract JSON from Response"]
    G --> I["Parse JSON Structure"]
    
    I --> J["Validate BPMN Format"]
    J --> K["BPMN 2.0 Valid"]
    
    K --> L["Save Results"]
    L --> M["bpmn_model.json"]
    L --> N["explanation.txt"]
    L --> O["full_response.txt"]
    L --> P["metadata.json"]
    
    M --> Q["output/modeler/{name}/"]
    N --> Q
    O --> Q
    P --> Q
```

### Orchestrator Agent Orchestrator

```mermaid
graph TD
    A["User Input"] --> B["OrchestratorAgent"]
    
    B --> C["Initialize Sub-agents"]
    C --> D["ParserAgent"]
    C --> E["ModelerAgent"]
    
    B --> F["Step 1: Parse"]
    F --> D
    D --> G{Parse<br/>Success?}
    
    G -->|No| H["Error Handling"]
    G -->|Yes| I["Save Parser Results"]
    
    I --> J["Step 2: Model"]
    J --> E
    E --> K{Model<br/>Success?}
    
    K -->|No| H
    K -->|Yes| L["Save Modeler Results"]
    
    L --> M["Step 3: Summary"]
    M --> N["Organize Output"]
    N --> O["Return Results"]
```

---

## API Design

### REST API Architecture

```mermaid
graph TD
    Client["HTTP Client"]
    
    Client -->|POST| A["POST /transform"]
    Client -->|GET| B["GET /results/{name}"]
    Client -->|GET| C["GET /download/{name}/{type}"]
    Client -->|GET| D["GET /processes"]
    Client -->|GET| E["GET /health"]
    
    A --> A1["Process Description"]
    A1 --> A2["Run OrchestratorAgent Workflow"]
    A2 --> A3["Return: status, files"]
    
    B --> B1["Get Process Results"]
    B1 --> B2["List Output Files"]
    B2 --> B3["Return: file metadata"]
    
    C --> C1["Download Specific File"]
    C1 --> C2["File Type: bpmn_model,<br/>elements, pseudocode, etc"]
    C2 --> C3["Return: file stream"]
    
    D --> D1["List All Processes"]
    D1 --> D2["Scan output/parser/"]
    D2 --> D3["Return: process list"]
    
    E --> E1["Health Check"]
    E1 --> E2["Return: status"]
```

### API Request/Response Models

```
ProcessTransformRequest:
├── process_description: str (min 10 chars)
├── process_name: str (min 1, max 100)
└── api_key: Optional[str]

ProcessingResult:
├── status: "success" | "error"
├── process_name: str
├── process_description: str
├── parser_status: str
├── modeler_status: str
├── files: Dict[FileInfo]
├── timestamp: str
└── error: Optional[str]

FileInfo:
├── filename: str
├── path: str
├── size: int
└── content_preview: Optional[str]
```

---

## Database Schema

### File System Organization

```
project_root/
├── output/
│   ├── parser/
│   │   └── {process_name}/
│   │       ├── elements.txt
│   │       ├── pseudocode.txt
│   │       ├── full_response.txt
│   │       ├── metadata.json
│   │       └── output.json
│   │
│   └── modeler/
│       └── {process_name}/
│           ├── bpmn_model.json
│           ├── explanation.txt
│           ├── full_response.txt
│           ├── metadata.json
│           └── output.json
│
├── config/
│   └── settings.py
├── agents/
│   ├── parser_agent.py
│   ├── modeler_agent.py
│   └── orchestrator_agent.py
├── prompts/
│   ├── parser_prompt.md
│   └── modeler_prompt.md
├── utils/
│   ├── file_handler.py
│   ├── json_parser.py
│   ├── text_formatter.py
│   └── error_handler.py
├── api/
│   └── server.py
└── main.py
```

### Metadata JSON Structure

```json
{
  "parser_metadata": {
    "model": "mistral-large-latest",
    "temperature": 0.2,
    "api_key_set": true,
    "usage": {
      "input_tokens": 1234,
      "output_tokens": 567
    }
  },
  "process_info": {
    "process_name": "customer_inquiry",
    "elements_count": 8,
    "pseudocode_lines": 12
  },
  "timestamp": "2024-01-15T10:30:00",
  "status": "success"
}
```

---

## Deployment Architecture

### Local Development Setup

```mermaid
graph TB
    Dev["Developer Machine"]
    
    subgraph Local["Local Environment"]
        Python["Python 3.12+"]
        venv[".venv"]
        Project["Project Code"]
        Config[".env Config"]
    end
    
    subgraph LocalServices["Local Services"]
        CLI["CLI: main.py"]
        API["API Server<br/>FastAPI"]
        FileSystem["File System<br/>output/"]
    end
    
    subgraph External["External Services"]
        MistralAPI["Mistral API"]
        Internet["Internet"]
    end
    
    Dev --> Local
    Local --> LocalServices
    LocalServices --> External
    External --> Internet
```

### Production Deployment (Docker)

```mermaid
graph TB
    Client["Client/User"]
    
    subgraph "Docker Container"
        Python["Python 3.12"]
        App["FastAPI App"]
        Config["Config"]
        Prompts["Prompts"]
    end
    
    subgraph "Volumes"
        Output["output/"]
        Logs["logs/"]
    end
    
    subgraph "External"
        MistralAPI["Mistral API"]
    end
    
    Client -->|HTTP| App
    App --> Config
    App --> Prompts
    App --> Output
    App --> Logs
    App --> MistralAPI
```

---

## Security Design

### Security Layers

```mermaid
graph TD
    A["API Request"]
    
    A --> B["Input Validation"]
    B --> C["Length Check"]
    B --> D["Format Check"]
    
    C --> E{Valid?}
    D --> E
    
    E -->|No| F["Reject - 400"]
    E -->|Yes| G["Process"]
    
    G --> H["API Key Validation"]
    H --> I{Key Valid?}
    
    I -->|No| J["Reject - 401"]
    I -->|Yes| K["Execute Workflow"]
    
    K --> L["Error Handling"]
    L --> M["Sanitize Errors"]
    M --> N["Log Securely"]
    N --> O["Return Safe Response"]
```

### Environment & Secrets

```
.env (git-ignored):
├── MISTRAL_API_KEY
├── API_PORT
└── DEBUG_MODE

.env.example (git-tracked):
├── MISTRAL_API_KEY=your-key-here
├── API_PORT=8000
└── DEBUG_MODE=false
```

---

## Error Handling & Logging

### Error Flow

```mermaid
graph TD
    A["Error Occurs"]
    
    A --> B{Error Type?}
    
    B -->|Validation| C["400 Bad Request"]
    B -->|Auth| D["401 Unauthorized"]
    B -->|Not Found| E["404 Not Found"]
    B -->|Rate Limit| F["429 Too Many Requests"]
    B -->|Server| G["500 Internal Error"]
    
    C --> H["Log Error"]
    D --> H
    E --> H
    F --> H
    G --> H
    
    H --> I["Sanitize Message"]
    I --> J["Return to Client"]
```
---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.12+ |
| **CLI Framework** | argparse |
| **Web Framework** | FastAPI + Uvicorn |
| **LLM** | Mistral AI |
| **LLM Client** | LangChain |
| **Request Library** | httpx |
| **Data Validation** | Pydantic |
| **Testing** | pytest |
| **Linting** | ruff |
| **Formatting** | black |
| **Package Manager** | uv |
| **Containerization** | Docker (future) |

---

## Summary

This system design provides:
- ✅ Clear separation of concerns
- ✅ Scalable architecture
- ✅ Security-first approach
- ✅ Comprehensive error handling
- ✅ Multiple input/output methods
- ✅ Production-ready design
- ✅ Clear deployment path