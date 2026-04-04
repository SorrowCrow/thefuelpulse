# Diesel Price News - Agent Workflow POC

A multi-agent system that uses Claude AI to generate a complete Astro website for tracking diesel fuel prices in Latvia.

## What This Does

This project demonstrates a **simple agentic workflow** using direct LLM API calls. Three AI agents collaborate to build a website:

1. **Planner Agent** - Reads requirements and designs the architecture
2. **Builder Agent** - Generates all code files (Astro components, pages, data)
3. **Reviewer Agent** - Reviews code quality and best practices

## Prerequisites

- Python 3.8+
- Anthropic API key ([get one here](https://console.anthropic.com/))

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up API Key

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your API key
# ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Run the Agent Workflow

```bash
python agents/run_poc.py
```

This will:
- Read `requirements.md`
- Call the Planner agent to create an architecture plan
- Call the Builder agent to generate all code files
- Call the Reviewer agent to validate the code
- Output everything to `output/` directory

### 4. Review the Output

Check the generated files:

```bash
ls -la output/
```

You'll find:
- `output/src/` - Generated Astro website files
- `output/*_output.txt` - Raw agent responses (for debugging)

### 5. Test the Website

To actually run the generated website:

```bash
# Go to output directory
cd output

# Install dependencies (if package.json was generated)
npm install

# Run dev server
npm run dev

# Open http://localhost:4321
```

## Project Structure

```
agentsCollab/
├── agents/
│   └── run_poc.py          # Main orchestration script
├── output/                 # Generated files (gitignored)
│   ├── src/                # Astro website files
│   ├── planner_output.txt  # Raw planner response
│   ├── builder_output.txt  # Raw builder response
│   └── reviewer_output.txt # Raw reviewer response
├── prompts/                # (Future: store prompt templates)
├── requirements.md         # Website requirements
├── requirements.txt        # Python dependencies
└── .env                    # Your API key (gitignored)
```

## How It Works

### Agent Orchestration Flow

```
requirements.md
      ↓
[Planner Agent]
      ↓
   (plan JSON)
      ↓
[Builder Agent]
      ↓
   (code files)
      ↓
[Write to output/]
      ↓
[Reviewer Agent]
      ↓
   (review report)
```

### Agent Roles

**Planner Agent:**
- Model: `claude-sonnet-4-5`
- Task: Design architecture, list all files needed
- Output: JSON with file manifest and design decisions

**Builder Agent:**
- Model: `claude-sonnet-4-5` (16K tokens)
- Task: Generate complete code files
- Output: JSON with file paths and content

**Reviewer Agent:**
- Model: `claude-sonnet-4-5`
- Task: Review code quality, best practices
- Output: JSON with verdict, score, findings

## Configuration

### Model Selection

Edit `agents/run_poc.py` to change models:

```python
# In call_agent method:
model="claude-sonnet-4-5"  # Change to claude-opus-4, claude-haiku-4, etc.
```

### Temperature

Adjust creativity vs consistency:

```python
temperature=0.3  # Lower = more consistent, Higher = more creative
```

### Max Tokens

Increase for larger outputs:

```python
max_tokens=16000  # Builder needs more tokens for code generation
```

## Cost Estimate

Approximate costs per run (as of March 2026):

- Planner: ~8K input + 2K output = ~$0.05
- Builder: ~10K input + 15K output = ~$0.25
- Reviewer: ~8K input + 2K output = ~$0.05

**Total: ~$0.35 per complete run**

## Troubleshooting

### "ANTHROPIC_API_KEY not found"

Make sure you:
1. Created `.env` file (copy from `.env.example`)
2. Added your API key to `.env`
3. API key starts with `sk-ant-`

### "No valid JSON found in response"

Sometimes agents don't format JSON perfectly. Check the raw output files:
- `output/planner_output.txt`
- `output/builder_output.txt`
- `output/reviewer_output.txt`

You can manually extract the JSON and fix formatting.

### Generated code has errors

The Reviewer agent will catch most issues. If the website doesn't work:
1. Check `output/reviewer_output.txt` for findings
2. Manually fix critical issues in `output/src/`
3. Re-run specific npm commands to test

## Next Steps

### Iteration 1: Add Retry Logic

Modify `run_poc.py` to re-prompt Builder if Reviewer finds FAIL verdict:

```python
if review["verdict"] == "FAIL":
    print("Reviewer failed - re-running builder with feedback...")
    files = self.run_builder(requirements, plan, feedback=review["findings"])
```

### Iteration 2: Migrate to CrewAI

Once you understand this flow, try using CrewAI for easier orchestration:
- Automatic context passing
- Built-in memory
- Task dependencies

### Iteration 3: Add More Agents

- **Backend Agent** - Generate API server code
- **Test Agent** - Write Playwright tests
- **Designer Agent** - Create color schemes and layouts

## Learning Resources

- [Anthropic API Docs](https://docs.anthropic.com/)
- [Astro Documentation](https://docs.astro.build/)
- [CrewAI Framework](https://docs.crewai.com/)
- [LangGraph Tutorial](https://langchain-ai.github.io/langgraph/)

## License

MIT
