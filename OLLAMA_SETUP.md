# Ollama Local Coding Tool Setup

## What This Is

A minimal command-line tool for delegating light coding tasks to a **local** Ollama instance. This keeps your code and sensitive data on your machine instead of sending it to cloud APIs.

## Prerequisites

### 1. Install Ollama

**Windows/Mac/Linux:**
- Download from https://ollama.ai
- Follow installation instructions

### 2. Pull a Coding Model

```bash
# Recommended: Qwen 2.5 Coder (7B)
ollama pull qwen2.5-coder:7b-instruct

# Alternative: DeepSeek Coder
ollama pull deepseek-coder:6.7b-instruct

# Alternative: CodeLlama
ollama pull codellama:7b-instruct
```

### 3. Start Ollama Server

```bash
ollama serve
```

Leave this running in a terminal. The API will be available at `http://localhost:11434`

## Usage

### Basic Syntax

```bash
python execution/ollama_chat.py --model MODEL_NAME --prompt "TASK"
```

### Example 1: Simple Code Generation

```bash
python execution/ollama_chat.py \
  --model qwen2.5-coder:7b-instruct \
  --prompt "Write a Python function to calculate the Fibonacci sequence up to n terms"
```

**Output:**
```python
def fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]

    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib
```

### Example 2: Request Unified Diff (for code changes)

```bash
python execution/ollama_chat.py \
  --model qwen2.5-coder:7b-instruct \
  --system "Output ONLY a unified diff patch. No explanations." \
  --prompt "Add type hints to this function:

def process_data(data):
    return data.strip().upper()"
```

**Output:**
```diff
--- a/script.py
+++ b/script.py
@@ -1,2 +1,2 @@
-def process_data(data):
-    return data.strip().upper()
+def process_data(data: str) -> str:
+    return data.strip().upper()
```

### Example 3: Read from Stdin

```bash
cat execution/fetch_emails.py | python execution/ollama_chat.py \
  --model qwen2.5-coder:7b-instruct \
  --prompt "Add docstrings to all functions in this code"
```

### Example 4: Generate JSON

```bash
python execution/ollama_chat.py \
  --model qwen2.5-coder:7b-instruct \
  --format json \
  --prompt "List 5 Python best practices as a JSON array"
```

### Example 5: Generate Unit Tests

```bash
python execution/ollama_chat.py \
  --model qwen2.5-coder:7b-instruct \
  --prompt "Write pytest unit tests for this function:

def calculate_total(items, tax_rate=0.1):
    subtotal = sum(item['price'] for item in items)
    tax = subtotal * tax_rate
    return subtotal + tax"
```

## Command-Line Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--model` | ✓ | - | Ollama model name (e.g., `qwen2.5-coder:7b-instruct`) |
| `--prompt` | * | stdin | User prompt (* optional if using stdin) |
| `--system` | ✗ | None | System prompt for behavior control |
| `--format` | ✗ | None | Response format (`json` for JSON output) |
| `--host` | ✗ | `http://localhost:11434` | Ollama API host |
| `--timeout` | ✗ | 600 | Request timeout in seconds |

## When to Use This

**✅ Good Use Cases:**
- Generate boilerplate code
- Refactor single functions
- Add type hints or docstrings
- Write unit tests
- Fix simple bugs
- Generate helper functions

**❌ Don't Use For:**
- Complex debugging requiring full codebase context
- Architecture decisions
- Multi-file refactoring
- Tasks requiring external API access
- System design

## Privacy Benefits

**Cloud AI (OpenAI/Anthropic):**
- ❌ Code sent over the internet
- ❌ Stored on their servers (30 days for OpenAI)
- ❌ Subject to their privacy policies

**Local Ollama:**
- ✅ Code never leaves your machine
- ✅ No internet connection required
- ✅ Complete privacy
- ✅ Works offline

**Use Ollama for:** Confidential business logic, client data processing, proprietary algorithms, sensitive email content.

## Troubleshooting

### Error: "Cannot connect to Ollama"

**Problem:** Ollama server isn't running.

**Solution:**
```bash
# Start Ollama server
ollama serve
```

### Error: "model not found"

**Problem:** Model not pulled.

**Solution:**
```bash
ollama pull qwen2.5-coder:7b-instruct
```

### Slow Response

**Problem:** Model is large or hardware is limited.

**Solutions:**
- Use a smaller model: `ollama pull qwen2.5-coder:1.5b-instruct`
- Increase timeout: `--timeout 1200`
- Check system resources (RAM, CPU)

### Bad Output Quality

**Problem:** Model doesn't understand the task.

**Solutions:**
- Be more specific in your prompt
- Use `--system` to set clear instructions
- Try a different model (e.g., `deepseek-coder:6.7b-instruct`)
- For code changes, always request "unified diff format"

## Integration with Claude Code

When using Claude Code with this repository, Claude can delegate coding tasks to Ollama automatically by following the protocol in `CLAUDE.md`:

```bash
# Claude will invoke:
python execution/ollama_chat.py \
  --model qwen2.5-coder:7b-instruct \
  --system "Output ONLY a unified diff patch." \
  --prompt "Add error handling to this function: ..."
```

See `CLAUDE.md` for the full delegation protocol.

## Performance Notes

**Hardware Requirements:**
- **Minimum:** 8GB RAM for 7B models
- **Recommended:** 16GB RAM for smooth performance
- **Optional:** GPU for faster inference

**Speed:**
- 7B models: ~5-15 tokens/second (CPU)
- 7B models: ~50-100 tokens/second (GPU)
- Smaller models (1.5B-3B): Faster but lower quality

## Recommended Models

| Model | Size | Best For |
|-------|------|----------|
| `qwen2.5-coder:7b-instruct` | 7B | General coding (recommended) |
| `qwen2.5-coder:1.5b-instruct` | 1.5B | Fast responses, simple tasks |
| `deepseek-coder:6.7b-instruct` | 6.7B | Code completion, debugging |
| `codellama:7b-instruct` | 7B | Python-focused tasks |
| `starcoder2:7b` | 7B | Multi-language support |

## Example Workflow

```bash
# 1. Generate a function
python execution/ollama_chat.py \
  --model qwen2.5-coder:7b-instruct \
  --prompt "Write a function to validate email addresses" > /tmp/email_validator.py

# 2. Review the output
cat /tmp/email_validator.py

# 3. If good, integrate into your codebase
# If needs changes, iterate with more specific prompts
```

## Dependencies

The script requires only the `requests` library, which is already in `requirements.txt`:

```bash
pip install requests
```

No additional dependencies needed.
