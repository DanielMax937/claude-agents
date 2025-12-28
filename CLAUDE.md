# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude-kit is a Python toolkit with two main components:

1. **Message Formatter**: Beautiful terminal formatting for Claude Agent SDK messages with colorized output for SystemMessage, AssistantMessage, UserMessage, and ResultMessage types
2. **Skill Wrapper**: Programmatic Python interface to execute Claude Code skills (options pricing, technical analysis, market data, etc.) from your scripts

## Commands

```bash
# Message Formatter demos
uv run python main.py              # Claude Agent SDK integration with session resumption
uv run python message_formatter.py # Message formatter demo
uv run python examples.py          # All example message types

# Skill Wrapper demos
uv run python skill_wrapper.py                # List available skills
uv run python examples/skill_wrapper_demo.py  # Comprehensive feature demo
uv run python examples/practical_example.py   # Real-world integration examples
```

## Architecture

### Message Formatter
- **message_formatter.py**: Core formatting logic
  - `Colors` class: ANSI color codes
  - `MessageFormatter` class: Main formatter with methods for each message type
  - Convenience functions: `format_message()`, `print_formatted()`

- **main.py**: Example integration with Claude Agent SDK showing:
  - Streaming messages via `query()`
  - Permission handlers
  - Hooks (PostToolUse)
  - Custom agents
  - MCP servers
  - Session resumption

### Skill Wrapper
- **skill_wrapper.py**: Core wrapper for programmatically calling Claude Code skills
  - `SkillWrapper` class: Main interface for skill execution
  - `SkillResult` dataclass: Structured execution results
  - `SkillOutputFormat` enum: Output formatting options (RAW, JSON, LINES, AUTO)
  - Convenience functions: `run_skill()`, `list_available_skills()`

- **examples/skill_wrapper_demo.py**: Comprehensive demo of all wrapper features
- **examples/practical_example.py**: Real-world integration patterns
- **SKILL_WRAPPER_GUIDE.md**: Complete API reference and quick-start guide

## Key Patterns

### 1. Formatting Claude Agent SDK Messages

```python
from message_formatter import MessageFormatter
formatter = MessageFormatter(use_colors=True)

async for message in query(prompt="...", options=ClaudeAgentOptions(...)):
    formatter.format_stream(message)
```

### 2. Calling Skills Programmatically

```python
from skill_wrapper import run_skill, SkillOutputFormat

# Simple execution
result = run_skill("options", "pricing",
                   args="--spot 100 --strike 105 --time 1 --rate 0.05 --vol 0.2")

if result.success:
    print(result.output)
else:
    print(f"Error: {result.error}")

# With JSON output
result = run_skill("options", "pricing",
                   args="--spot 100 --strike 105 --time 1 --rate 0.05 --vol 0.2 --json",
                   output_format=SkillOutputFormat.JSON)
```

### 3. Skill Pipeline

```python
from skill_wrapper import SkillWrapper

wrapper = SkillWrapper()
commands = [
    {"skill_name": "options", "script_name": "pricing",
     "args": "--spot 100 --strike 105 --time 1 --rate 0.05 --vol 0.2"},
    {"skill_name": "options", "script_name": "greeks",
     "args": "--spot 100 --strike 105 --time 1 --rate 0.05 --vol 0.2"},
]
results = wrapper.run_pipeline(commands)
```

### 4. Integrated Pattern (Formatter + Wrapper)

```python
from skill_wrapper import run_skill
from message_formatter import MessageFormatter

formatter = MessageFormatter(use_colors=True)
result = run_skill("options", "pricing",
                   "--spot 100 --strike 105 --time 1 --rate 0.05 --vol 0.2")

if result.success:
    print(formatter.colors.header("📊 Result"))
    print(formatter.colors.green("✓ Success\n"))
    print(formatter.colors.text(result.output))
```

### Message Type Detection

The formatter auto-detects types via class names or attribute inspection:
- `SystemMessage`: has `subtype` and `data`
- `AssistantMessage`: has `content` list and `model`
- `UserMessage`: has `uuid` and `content` list (no `model`)
- `ResultMessage`: has `subtype`, `duration_ms`, and `usage`

### Content Blocks

AssistantMessage content blocks: TextBlock, ThinkingBlock, ToolUseBlock, ToolResultBlock

## Dependencies

- `claude-agent-sdk>=0.1.18`
- `python-dotenv` (for loading .env)
