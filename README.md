# Claude Agent Message Formatter

A beautiful Python utility to format Claude agent messages with colors, spacing, and structured layouts. Fully compatible with the Claude Agent SDK.

## Features

✨ **Beautiful Colors** - ANSI color codes for different message types
📦 **Smart Formatting** - Automatically detects and formats different message types
⏰ **Timestamps** - Adds timestamps to each message
🎨 **Customizable** - Configure colors, indentation, and more
📊 **Multiple Types** - Supports SystemMessage, AssistantMessage, ResultMessage, and more
🚫 **No Truncation** - Displays complete content without cutting off text
🧠 **Rich Content** - Handles TextBlock, ThinkingBlock, ToolUseBlock, ToolResultBlock
💰 **Cost Tracking** - Shows token usage, costs, and timing information

## Installation

No additional dependencies required! Uses Python's built-in libraries.

## Quick Start

### Basic Usage

```python
from message_formatter import MessageFormatter

# Create formatter
formatter = MessageFormatter()

# Format a simple message
message = "Hello from Claude!"
formatter.format_stream(message)
```

### With Claude Agent SDK

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions
from message_formatter import MessageFormatter

async def main():
    formatter = MessageFormatter(use_colors=True)

    async for message in query(
        prompt="Your prompt here",
        options=ClaudeAgentOptions(...)
    ):
        formatter.format_stream(message)

asyncio.run(main())
```

### Quick Functions

```python
from message_formatter import print_formatted, format_message

# Print formatted message directly
print_formatted({"type": "text", "content": "Hello!"})

# Get formatted string
formatted = format_message({"type": "tool_use", "name": "Read"})
print(formatted)
```

## Message Types

The formatter automatically detects and beautifully formats these message types:

### 🔧 SystemMessage (Claude Agent SDK)
Displays system-level messages with metadata.

```python
from claude_agent_sdk.types import SystemMessage

sys_msg = SystemMessage(
    subtype='system_prompt',
    data={'content': 'You are a helpful assistant.'}
)
formatter.format_stream(sys_msg)
```

**Output includes:**
- Message subtype
- All data fields (no truncation)
- Structured display with proper indentation

### 🤖 AssistantMessage (Claude Agent SDK)
Comprehensive formatting for Claude's responses with multiple content blocks.

```python
from claude_agent_sdk.types import AssistantMessage, TextBlock, ToolUseBlock

msg = AssistantMessage(
    content=[
        TextBlock(text="Let me help you with that."),
        ToolUseBlock(id='toolu_123', name='Read', input={'file_path': '/path/to/file'})
    ],
    model='claude-3-5-sonnet-20241022'
)
formatter.format_stream(msg)
```

**Supports all content block types:**
- 💬 **TextBlock**: Plain text responses
- 🧠 **ThinkingBlock**: Claude's internal reasoning (with signature)
- 🔧 **ToolUseBlock**: Tool invocations with full input parameters
- ✅ **ToolResultBlock**: Tool results with complete content (no truncation)

**Output includes:**
- Model name
- Parent tool use ID (if nested)
- Error status (if present)
- Complete content from all blocks
- Numbered block list for easy reference

### ✅ ResultMessage (Claude Agent SDK)
Detailed statistics and final results from agent queries.

```python
# ResultMessage is returned by query() in the Claude Agent SDK
# The formatter automatically detects and displays it beautifully
```

**Output includes:**
- ⏱️ **Timing**: Total and API duration
- 🔄 **Session**: Session ID and turn count
- 💰 **Cost**: Total cost in USD
- 📊 **Token Usage**: Input, cache creation, cache read, output tokens
- 🔧 **Server Tools**: Web search and fetch request counts
- 📝 **Result**: Complete result text (no truncation)
- 🗂️ **Structured Output**: Any structured data returned

### 💬 Text Messages (Legacy Format)
```python
{"type": "text", "content": "This is a text message"}
```

### 🔧 Tool Use (Legacy Format)
```python
{
    "type": "tool_use",
    "name": "Read",
    "input": {"file_path": "/path/to/file.py"}
}
```

### 📋 Tool Results (Legacy Format)
```python
{
    "type": "tool_result",
    "tool_use_id": "toolu_123",
    "content": "Result content"
}
```

### ❌ Errors (Legacy Format)
```python
{"type": "error", "error": "Error message"}
```

### 📦 Custom Messages
Any dictionary or string will be formatted appropriately.

## Configuration

```python
formatter = MessageFormatter(
    use_colors=True,  # Enable/disable ANSI colors
    indent=2          # Number of spaces for indentation
)
```

## Color Scheme

### Claude Agent SDK Messages
- **SystemMessage**: Bright Blue (🔧)
- **AssistantMessage**: Bright Green (🤖) / Bright Red (❌) for errors
- **ResultMessage**: Bright Green (✅) / Bright Red (❌) for errors

### Content Blocks
- **TextBlock**: Bright Green (💬)
- **ThinkingBlock**: Bright Magenta (🧠)
- **ToolUseBlock**: Bright Blue (🔧)
- **ToolResultBlock**: Bright Green (✅) / Bright Red (❌) for errors

### Legacy Format
- **Text Messages**: Bright Green (💬)
- **Tool Use**: Bright Blue (🔧)
- **Tool Results**: Bright Magenta (📋)
- **Errors**: Bright Red (❌)
- **Generic Messages**: Bright Cyan (📦)

## Demo

Run the demos to see all formatting options:

```bash
# Demo all message types
python test_all_messages.py

# Demo legacy format
python message_formatter.py

# Demo ResultMessage
python test_result_message.py

# See real-world usage
python main.py
```

## Disable Colors

For logging to files or non-terminal output:

```python
formatter = MessageFormatter(use_colors=False)
```

## Examples

Check out the example files:
- `main.py` - Complete example with Claude Agent SDK
- `test_all_messages.py` - Comprehensive test of all message types
- `test_result_message.py` - ResultMessage formatting examples
- `examples.py` - Legacy format examples

## Key Features

### No Truncation
Unlike the previous version, **all content is displayed in full**. No more truncated results or "..." indicators. Perfect for debugging and understanding exactly what Claude is processing.

### Rich Content Block Support
The AssistantMessage formatter handles all content block types:
- Multiple text blocks in sequence
- Thinking blocks with reasoning and signatures
- Tool use blocks with complete input parameters
- Tool result blocks with full output content

### Comprehensive Statistics
ResultMessage displays detailed information about:
- Execution timing (total and API)
- Token usage breakdown (input, cache creation, cache read, output)
- Cost tracking in USD
- Service tier information
- Server tool usage statistics

### Automatic Detection
The formatter automatically detects the message type based on its structure and attributes, so you don't need to specify what kind of message you're formatting.

## License

MIT License - Feel free to use and modify!
