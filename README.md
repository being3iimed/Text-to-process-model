# Text to Process Model

Transform natural language business process descriptions into BPMN 2.0 models (.json format) agentic pipeline.

## Overview

This project automates the conversion of natural language process descriptions into BPMN (Business Process Model and Notation) 2.0 JSON models that needs to be converted (BPMN-MODDLE Library) and then can be imported into tools like:
- [Camunda Modeler](https://camunda.com/products/camunda-modeler/)
- [draw.io](https://draw.io)
- [BPMN.io](https://bpmn.io)
- 
### Workflow

```
Natural Language Description
        ↓
    [Parser Agent]
        ↓
Process Elements + Pseudocode
        ↓
   [Modeler Agent]
        ↓
BPMN 2.0 JSON Model
```

## Features

- 🤖 **AI-Powered Parsing** - Uses Mistral LLM to understand natural language processes
- 📊 **Structured Element Extraction** - Identifies tasks, events, gateways, and flows
- 📐 **BPMN 2.0 Generation** - Creates valid, executable BPMN models
- 💾 **Organized Output** - Saves elements, pseudocode, models, and metadata
- 🔄 **Complete Workflow** - End-to-end process transformation
- 📁 **Multiple Input Modes** - Interactive, file-based, or direct content input

## Requirements

- Python 3.11+ (3.12+ recommended)
- Mistral API key ([get one here](https://console.mistral.ai/))
- `uv` package manager (or `pip`)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/being3iimed/text-to-process-model.git
cd text-to-process-model
```

### 2. Set Up Python Environment

```bash
# Using uv (recommended)
uv venv
uv sync

# Or using pip
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 3. Configure API Key

Create a `.env` file in the project root:

```bash
MISTRAL_API_KEY=your-mistral-api-key-here
```

Or set as environment variable:

```bash
# PowerShell (Windows)
$env:MISTRAL_API_KEY = "your-key"

# Bash (macOS/Linux)
export MISTRAL_API_KEY="your-key"
```

## Usage

### Interactive Mode (Recommended)

```bash
python main.py
```

Then:
1. Paste your process description (multiple lines OK)
2. Type `END` when done
3. Enter a name for the process
4. Wait for BPMN model to be generated

Example:

```
This process begins when a customer inquires about a product. 
Sales staff collects information and addresses concerns. 
If interested, they guide through product selection and provide a quote. 
After approval, the order is placed and recorded in the system.
END
```

### From File

```bash
python main.py --input path/to/process.txt --name my_process
```

### Direct Content

```bash
python main.py --content "Your process description here" --name quick_process
```

### With Custom Options

```bash
python main.py \
  --input process.txt \
  --name customer_inquiry \
  --api-key your-custom-key \
  --verbose \
  --output-json
```

## Options

| Flag | Description |
|------|-------------|
| `--input, -i` | Path to input file with process description |
| `--content, -c` | Direct process description text |
| `--name, -n` | Process name for organizing outputs |
| `--api-key` | Custom Mistral API key |
| `--verbose, -v` | Enable detailed output |
| `--output-json` | Output results as JSON |


  --output-json
```

## Performance Evaluation

The project includes tools to analyze agent performance using LangSmith data.

### Prerequisites
```bash
pip install langsmith pandas
```

### Running the Evaluation Pipeline

1.  **Fetch & Enrich Data**:
    Connects to LangSmith, fetches runs, and injects local metadata (Agent, Process, Stage).
    ```bash
    python evals/process_langsmith_data.py
    ```

2.  **Generate Report**:
    Aggregates metrics (latency, tokens) and saves a summary to `evals/performance_report.txt`.
    ```bash
    python evals/performance.py
    ```

## Batch processing (new)

Transform **many** process descriptions in one shot.  
Descriptions are read from `input/processes.json` (category → process → description).

# all processes
python batch_main.py

# one category
python batch_main.py --category retail

# single process
python batch_main.py --category retail --process checkout_process

# extra options
python batch_main.py --verbose --stop-on-error --no-convert   # skip BPMN XML step
  
```json
// input/processes.json example
{
  "retail": {
    "checkout_process": "Customer adds items to cart → proceeds to checkout → pays → receives confirmation",
    "return_process":   "Customer requests return → agent validates → refund issued"
  },
  "finance": {
    "loan_approval":    "Applicant submits form → risk score → manager approval → loan granted"
  }
}
```
## Output Structure

```
output/
├── parser/
│   └── {process_name}/
│       ├── elements.txt          # Extracted process elements
│       ├── pseudocode.txt        # Pseudocode representation
│       ├── full_response.txt     # Complete parser response
│       ├── metadata.json         # Parser metadata
│       └── output.json           # Combined output
└── modeler/
    └── {process_name}/
        ├── bpmn_model.json       # ← BPMN 2.0 model (import to tools)
        ├── explanation.txt       # Model explanation
        ├── full_response.txt     # Complete modeler response
        ├── metadata.json         # Modeler metadata
        └── output.json           # Combined output
```
│   ├── file_handler.py           # File I/O utilities
│   ├── json_parser.py            # JSON extraction utilities
│   ├── text_formatter.py         # Text formatting utilities
│   └── error_handler.py          # Error handling
├── output/                        # Generated outputs (git-ignored)
├── main.py                       # Entry point
├── requirements.txt              # Python dependencies
├── pyproject.toml                # Project configuration
├── .env                          # Environment variables (git-ignored)
└── README.md                     # This file
```

## How It Works

### 1. Parser Agent

- Receives natural language process description
- Uses Mistral LLM with custom prompt to analyze
- Extracts structured elements:
  - **Tasks**: User tasks, service tasks, manual tasks
  - **Events**: Start, end, intermediate events
  - **Gateways**: Exclusive, parallel, inclusive
  - **Flows**: Sequence flows with conditions
- Generates pseudocode representation

### 2. Modeler Agent

- Receives parsed pseudocode and elements
- Generates BPMN 2.0 JSON model
- Ensures:
  - Valid JSON structure
  - Unique, consistent element IDs
  - Proper flow logic
  - Importable into BPMN tools
- Provides explanation of design decisions

### 3. Output Management

- Saves all intermediate results
- Organizes by process name
- Stores metadata (tokens, timestamps, etc.)
- Generates both individual files and combined JSON

## Configuration

Edit `config/settings.py` to customize:

```python
# API Configuration
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = "mistral-large-latest"  # Change model here

# Output Configuration
OUTPUT_DIR = Path("output")
PROMPTS_DIR = Path("prompts")

# Default Input
DEFAULT_INPUT = "input/default.txt"
```

## Example Process Flow

### Input
```
Customer inquiry process: A customer contacts sales. 
Staff collects info and addresses questions. 
If interested, guide through product selection, 
provide quote, get approval, place order, 
record in system, send confirmation.
```

### Generated BPMN (elements)
```
- Start Event: Customer Inquiry
- User Task: Collect Information
- User Task: Address Questions
- Exclusive Gateway: Customer Interested?
- User Task: Guide Product Selection
- User Task: Provide Quote
- User Task: Get Approval
- Service Task: Place Order
- Service Task: Record Order
- Send Task: Confirmation
- End Event: Process Complete
```

### Output File
```json
{
  "definitions": {
    "id": "customer-inquiry-process",
    "rootElements": [
      {
        "id": "Process_1",
        "flowElements": [
          {
            "id": "StartEvent_1",
            "type": "bpmn:StartEvent",
            "name": "Customer Inquiry"
          },
          ...
        ]
      }
    ]
  }
}
```

## Troubleshooting

### 401 Unauthorized Error
- Verify `MISTRAL_API_KEY` is set correctly
- Check API key has appropriate permissions
- Ensure `.env` file exists and is properly formatted

### 429 Rate Limit Error
- Wait a few minutes and retry
- Consider using a smaller model: `mistral-small-latest`
- Check your Mistral plan quotas

### File Not Found Error
- Ensure input file path is correct
- Check file encoding is UTF-8
- Verify file exists and is readable

### Empty or Incomplete Output
- Input description may be too vague
- Try more detailed process description
- Check parser and modeler logs for details

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -am 'Add improvement'`)
4. Push to branch (`git push origin feature/improvement`)
5. Open a Pull Request

## Development

### Running Tests

```bash
pytest tests/
```

### Linting

```bash
ruff check .
black --check .
```

### Formatting

```bash
black .
```

## API Costs

This project uses the Mistral API. Costs depend on:
- Number of API calls
- Length of input/output
- Model used

Monitor usage at [Mistral Console](https://console.mistral.ai/)

## Limitations

- Model accuracy depends on input clarity
- Complex processes may require multiple refinements
- BPMN model complexity scales with process description
- API rate limits apply based on subscription tier

## Future Enhancements

- [ ] Support for multiple LLM providers (OpenAI, Claude, etc.)
- [ ] Interactive BPMN editor integration
- [ ] Model validation and quality scoring
- [ ] Batch process generation
- [ ] Process simulation from BPMN model
- [ ] Model versioning and comparison
- [ ] Export to additional formats (XML, XPDL)

## License

MIT License - see LICENSE file for details

## Support

- 📧 Email: imed.k@outlook.com
- 🐛 Issues: [GitHub Issues](https://github.com/being3iimed/text-to-process-model/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/being3iimed/text-to-process-model/discussions)

## Acknowledgments

- [Mistral AI](https://mistral.ai/) - LLM provider
- [LangChain](https://langchain.com/) - LLM framework
- [BPMN.io](https://bpmn.io) - BPMN reference implementation
- [Camunda](https://camunda.com/) - BPMN tooling

## Changelog

### v1.0.0 (Initial Release)
- Core parser agent for process description analysis
- BPMN 2.0 model generation
- File management and organization
- Interactive CLI interface
- Support for multiple input modes