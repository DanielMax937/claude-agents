"""
Claude Agent Message Formatter
A utility to beautifully format Claude agent messages with colors and spacing.
"""

from typing import Any
import json
from datetime import datetime


class Colors:
    """ANSI color codes for terminal output"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright foreground colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


class MessageFormatter:
    """Formats Claude agent messages with beautiful colors and spacing"""

    def __init__(self, use_colors: bool = True, indent: int = 2):
        """
        Initialize the formatter

        Args:
            use_colors: Whether to use ANSI colors (set to False for non-terminal output)
            indent: Number of spaces for indentation
        """
        self.use_colors = use_colors
        self.indent = indent
        self.separator = "─" * 80

    def _color(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled"""
        if not self.use_colors:
            return text
        return f"{color}{text}{Colors.RESET}"

    def _format_timestamp(self) -> str:
        """Format current timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        return self._color(f"[{timestamp}]", Colors.BRIGHT_BLACK)

    def _format_header(self, title: str, color: str = Colors.BRIGHT_CYAN) -> str:
        """Format a section header"""
        header = f"╭─ {title} "
        padding = "─" * (80 - len(header) - 1)
        full_header = f"{header}{padding}╮"
        return self._color(full_header, color)

    def _format_footer(self) -> str:
        """Format a section footer"""
        footer = "╰" + "─" * 78 + "╯"
        return self._color(footer, Colors.BRIGHT_BLACK)

    def _format_key_value(self, key: str, value: Any, indent_level: int = 0) -> str:
        """Format a key-value pair"""
        indent_str = " " * (self.indent * indent_level)
        key_colored = self._color(key, Colors.BRIGHT_YELLOW)

        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, indent=2, ensure_ascii=False)
            return f"{indent_str}{key_colored}: {value_str}"
        elif isinstance(value, bool):
            value_colored = self._color(str(value), Colors.BRIGHT_MAGENTA)
        elif isinstance(value, (int, float)):
            value_colored = self._color(str(value), Colors.BRIGHT_BLUE)
        elif value is None:
            value_colored = self._color("null", Colors.DIM)
        else:
            value_colored = self._color(str(value), Colors.WHITE)

        return f"{indent_str}{key_colored}: {value_colored}"

    def _format_system_message(self, message: Any) -> list:
        """Format a SystemMessage object"""
        lines = []

        # Get attributes
        subtype = getattr(message, 'subtype', 'unknown')
        data = getattr(message, 'data', {})

        # Header
        lines.append(self._format_header(f"🔧 System Message - {subtype.title()}", Colors.BRIGHT_BLUE))
        lines.append("")

        # Subtype
        lines.append(self._format_key_value("Type", self._color(subtype, Colors.BRIGHT_BLUE), 1))

        # Data content
        if data:
            lines.append("")
            lines.append(self._color("  📦 Data:", Colors.BRIGHT_CYAN))

            # Format data based on type and content
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, str):
                        # Don't truncate - show full content
                        lines.append(self._format_key_value(f"  {key}", "", 0))
                        lines.append(self._indent_text(value, 2))
                    else:
                        lines.append(self._format_key_value(f"  {key}", value, 1))
            else:
                lines.append(self._indent_text(str(data), 2))

        return lines

    def _format_assistant_message(self, message: Any) -> list:
        """Format an AssistantMessage object with all content blocks"""
        lines = []

        # Get attributes
        content = getattr(message, 'content', [])
        model = getattr(message, 'model', 'unknown')
        parent_tool_use_id = getattr(message, 'parent_tool_use_id', None)
        error = getattr(message, 'error', None)

        # Header with status
        if error:
            lines.append(self._format_header("❌ Assistant Message - Error", Colors.BRIGHT_RED))
        else:
            lines.append(self._format_header("🤖 Assistant Message", Colors.BRIGHT_GREEN))

        lines.append("")

        # Model info
        lines.append(self._format_key_value("Model", self._color(model, Colors.BRIGHT_CYAN), 1))

        # Parent tool use ID (if present)
        if parent_tool_use_id:
            lines.append(self._format_key_value("Parent Tool Use ID", parent_tool_use_id, 1))

        # Error (if present)
        if error:
            lines.append("")
            lines.append(self._color("  ❌ Error:", Colors.BRIGHT_RED))
            lines.append(self._indent_text(str(error), 2))

        # Content blocks
        if content:
            lines.append("")
            lines.append(self._color(f"  📝 Content ({len(content)} block(s)):", Colors.BRIGHT_CYAN))

            for idx, block in enumerate(content, 1):
                lines.append("")
                block_type = type(block).__name__

                # Format based on block type
                if block_type == 'TextBlock':
                    text = getattr(block, 'text', '')
                    lines.append(self._color(f"    [{idx}] 💬 Text Block:", Colors.BRIGHT_GREEN))
                    lines.append(self._indent_text(text, 3))

                elif block_type == 'ThinkingBlock':
                    thinking = getattr(block, 'thinking', '')
                    signature = getattr(block, 'signature', '')
                    lines.append(self._color(f"    [{idx}] 🧠 Thinking Block:", Colors.BRIGHT_MAGENTA))
                    lines.append(self._indent_text(thinking, 3))
                    if signature:
                        lines.append("")
                        lines.append(self._color("      Signature:", Colors.DIM))
                        lines.append(self._indent_text(signature, 4))

                elif block_type == 'ToolUseBlock':
                    tool_id = getattr(block, 'id', '')
                    tool_name = getattr(block, 'name', '')
                    tool_input = getattr(block, 'input', {})
                    lines.append(self._color(f"    [{idx}] 🔧 Tool Use Block:", Colors.BRIGHT_BLUE))
                    lines.append(self._format_key_value("      ID", tool_id, 0))
                    lines.append(self._format_key_value("      Tool", self._color(tool_name, Colors.BRIGHT_YELLOW), 0))
                    if tool_input:
                        lines.append(self._color("      Input:", Colors.BRIGHT_CYAN))
                        if isinstance(tool_input, dict):
                            for key, value in tool_input.items():
                                # Format input values nicely
                                if isinstance(value, str) and len(value) > 100:
                                    lines.append(self._format_key_value(f"        {key}", f"{value[:100]}... ({len(value)} chars)", 0))
                                else:
                                    lines.append(self._format_key_value(f"        {key}", value, 0))
                        else:
                            lines.append(self._indent_text(str(tool_input), 4))

                elif block_type == 'ToolResultBlock':
                    tool_use_id = getattr(block, 'tool_use_id', '')
                    result_content = getattr(block, 'content', '')
                    is_error = getattr(block, 'is_error', False)

                    if is_error:
                        lines.append(self._color(f"    [{idx}] ❌ Tool Result Block (Error):", Colors.BRIGHT_RED))
                    else:
                        lines.append(self._color(f"    [{idx}] ✅ Tool Result Block:", Colors.BRIGHT_GREEN))

                    lines.append(self._format_key_value("      Tool Use ID", tool_use_id, 0))

                    if result_content:
                        lines.append(self._color("      Content:", Colors.BRIGHT_CYAN))
                        if isinstance(result_content, str):
                            # Don't truncate - show full content
                            lines.append(self._indent_text(result_content, 4))
                        elif isinstance(result_content, list):
                            lines.append(self._indent_text(json.dumps(result_content, indent=2), 4))
                        else:
                            lines.append(self._indent_text(str(result_content), 4))

                else:
                    # Unknown block type
                    lines.append(self._color(f"    [{idx}] 📦 {block_type}:", Colors.BRIGHT_CYAN))
                    lines.append(self._indent_text(str(block), 3))

        return lines

    def _format_user_message(self, message: Any) -> list:
        """Format a UserMessage object with tool results"""
        lines = []

        # Get attributes
        content = getattr(message, 'content', [])
        uuid = getattr(message, 'uuid', None)
        parent_tool_use_id = getattr(message, 'parent_tool_use_id', None)

        # Header
        lines.append(self._format_header("👤 User Message", Colors.BRIGHT_CYAN))
        lines.append("")

        # UUID (if present)
        if uuid:
            lines.append(self._format_key_value("UUID", uuid, 1))

        # Parent tool use ID (if present)
        if parent_tool_use_id:
            lines.append(self._format_key_value("Parent Tool Use ID", parent_tool_use_id, 1))

        # Content blocks
        if content:
            lines.append("")
            lines.append(self._color(f"  📝 Content ({len(content)} block(s)):", Colors.BRIGHT_CYAN))

            for idx, block in enumerate(content, 1):
                lines.append("")
                block_type = type(block).__name__

                # Format based on block type
                if block_type == 'ToolResultBlock':
                    tool_use_id = getattr(block, 'tool_use_id', '')
                    result_content = getattr(block, 'content', '')
                    is_error = getattr(block, 'is_error', False)

                    if is_error:
                        lines.append(self._color(f"    [{idx}] ❌ Tool Result Block (Error):", Colors.BRIGHT_RED))
                    else:
                        lines.append(self._color(f"    [{idx}] ✅ Tool Result Block:", Colors.BRIGHT_GREEN))

                    lines.append(self._format_key_value("      Tool Use ID", tool_use_id, 0))

                    if result_content:
                        lines.append(self._color("      Content:", Colors.BRIGHT_CYAN))
                        if isinstance(result_content, str):
                            # Don't truncate - show full content
                            lines.append(self._indent_text(result_content, 4))
                        elif isinstance(result_content, list):
                            lines.append(self._indent_text(json.dumps(result_content, indent=2), 4))
                        else:
                            lines.append(self._indent_text(str(result_content), 4))

                elif block_type == 'TextBlock':
                    text = getattr(block, 'text', '')
                    lines.append(self._color(f"    [{idx}] 💬 Text Block:", Colors.BRIGHT_GREEN))
                    lines.append(self._indent_text(text, 3))

                else:
                    # Unknown block type
                    lines.append(self._color(f"    [{idx}] 📦 {block_type}:", Colors.BRIGHT_CYAN))
                    lines.append(self._indent_text(str(block), 3))

        return lines

    def _format_result_message(self, message: Any) -> list:
        """Format a ResultMessage object with detailed statistics"""
        lines = []

        # Determine if it's an error or success
        is_error = getattr(message, 'is_error', False)
        subtype = getattr(message, 'subtype', 'unknown')

        # Header with status
        if is_error:
            lines.append(self._format_header("❌ Result Message - Error", Colors.BRIGHT_RED))
        else:
            lines.append(self._format_header("✅ Result Message - Success", Colors.BRIGHT_GREEN))

        lines.append("")

        # Status and type
        status_color = Colors.RED if is_error else Colors.GREEN
        lines.append(self._format_key_value("Status", self._color(subtype.upper(), status_color), 1))

        # Timing information
        duration_ms = getattr(message, 'duration_ms', 0)
        duration_api_ms = getattr(message, 'duration_api_ms', 0)
        if duration_ms or duration_api_ms:
            lines.append("")
            lines.append(self._color("  ⏱️  Timing:", Colors.BRIGHT_CYAN))
            if duration_ms:
                lines.append(self._format_key_value("  Total Duration", f"{duration_ms:,} ms ({duration_ms/1000:.2f}s)", 1))
            if duration_api_ms:
                lines.append(self._format_key_value("  API Duration", f"{duration_api_ms:,} ms ({duration_api_ms/1000:.2f}s)", 1))

        # Session information
        session_id = getattr(message, 'session_id', None)
        num_turns = getattr(message, 'num_turns', None)
        if session_id or num_turns:
            lines.append("")
            lines.append(self._color("  🔄 Session:", Colors.BRIGHT_CYAN))
            if session_id:
                lines.append(self._format_key_value("  Session ID", session_id, 1))
            if num_turns is not None:
                lines.append(self._format_key_value("  Turns", num_turns, 1))

        # Cost information
        total_cost = getattr(message, 'total_cost_usd', None)
        if total_cost is not None:
            lines.append("")
            lines.append(self._color("  💰 Cost:", Colors.BRIGHT_YELLOW))
            lines.append(self._format_key_value("  Total Cost", f"${total_cost:.6f} USD", 1))

        # Usage statistics
        usage = getattr(message, 'usage', None)
        if usage:
            lines.append("")
            lines.append(self._color("  📊 Token Usage:", Colors.BRIGHT_MAGENTA))

            # Input tokens
            input_tokens = usage.get('input_tokens', 0)
            cache_creation = usage.get('cache_creation_input_tokens', 0)
            cache_read = usage.get('cache_read_input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)

            lines.append(self._format_key_value("  Input Tokens", f"{input_tokens:,}", 1))
            if cache_creation:
                lines.append(self._format_key_value("  Cache Creation", f"{cache_creation:,}", 1))
            if cache_read:
                lines.append(self._format_key_value("  Cache Read", f"{cache_read:,}", 1))
            lines.append(self._format_key_value("  Output Tokens", f"{output_tokens:,}", 1))

            # Total tokens
            total_tokens = input_tokens + cache_creation + cache_read + output_tokens
            lines.append(self._format_key_value("  Total Tokens", self._color(f"{total_tokens:,}", Colors.BRIGHT_WHITE), 1))

            # Service tier
            service_tier = usage.get('service_tier', None)
            if service_tier:
                lines.append(self._format_key_value("  Service Tier", service_tier, 1))

            # Server tool use
            server_tool_use = usage.get('server_tool_use', {})
            if server_tool_use:
                web_search = server_tool_use.get('web_search_requests', 0)
                web_fetch = server_tool_use.get('web_fetch_requests', 0)
                if web_search or web_fetch:
                    lines.append("")
                    lines.append(self._color("  🔧 Server Tools:", Colors.BRIGHT_BLUE))
                    if web_search:
                        lines.append(self._format_key_value("  Web Search", web_search, 1))
                    if web_fetch:
                        lines.append(self._format_key_value("  Web Fetch", web_fetch, 1))

        # Result content (if present) - NO TRUNCATION
        result = getattr(message, 'result', None)
        if result:
            lines.append("")
            lines.append(self._color("  📝 Result:", Colors.BRIGHT_CYAN))
            lines.append(self._indent_text(str(result), 2))

        # Structured output (if present)
        structured_output = getattr(message, 'structured_output', None)
        if structured_output is not None:
            lines.append("")
            lines.append(self._color("  🗂️  Structured Output:", Colors.BRIGHT_CYAN))
            lines.append(self._indent_text(str(structured_output), 2))

        return lines

    def format_message(self, message: Any) -> str:
        """
        Format a Claude agent message

        Args:
            message: The message object to format

        Returns:
            Formatted string with colors and spacing
        """
        lines = []

        # Add timestamp
        lines.append(self._format_timestamp())
        lines.append("")

        # Check message type and format accordingly
        message_class_name = type(message).__name__

        # SystemMessage: has 'subtype' and 'data' attributes
        if message_class_name == 'SystemMessage' or (hasattr(message, 'subtype') and hasattr(message, 'data') and not hasattr(message, 'duration_ms')):
            lines.extend(self._format_system_message(message))

        # UserMessage: has 'uuid' and 'content' list, but not 'model'
        elif message_class_name == 'UserMessage' or (hasattr(message, 'uuid') and hasattr(message, 'content') and not hasattr(message, 'model') and isinstance(getattr(message, 'content', None), list)):
            lines.extend(self._format_user_message(message))

        # AssistantMessage: has 'content' list and 'model' attributes
        elif message_class_name == 'AssistantMessage' or (hasattr(message, 'content') and hasattr(message, 'model') and isinstance(getattr(message, 'content', None), list)):
            lines.extend(self._format_assistant_message(message))

        # ResultMessage: has 'subtype', 'duration_ms', and 'usage' attributes
        elif message_class_name == 'ResultMessage' or (hasattr(message, 'subtype') and hasattr(message, 'duration_ms') and hasattr(message, 'usage')):
            lines.extend(self._format_result_message(message))

        # Handle different message types
        elif isinstance(message, dict):
            # Check for specific message types
            if "type" in message:
                msg_type = message.get("type", "unknown")

                # Format based on message type
                if msg_type == "text":
                    lines.append(self._format_header("💬 Text Message", Colors.BRIGHT_GREEN))
                    lines.append("")
                    content = message.get("content", "")
                    lines.append(self._indent_text(content, 1))

                elif msg_type == "tool_use":
                    lines.append(self._format_header("🔧 Tool Use", Colors.BRIGHT_BLUE))
                    lines.append("")
                    lines.append(self._format_key_value("Tool", message.get("name", "unknown"), 1))
                    if "input" in message:
                        lines.append(self._format_key_value("Input", message["input"], 1))

                elif msg_type == "tool_result":
                    lines.append(self._format_header("📋 Tool Result", Colors.BRIGHT_MAGENTA))
                    lines.append("")
                    lines.append(self._format_key_value("Tool ID", message.get("tool_use_id", "unknown"), 1))
                    if "content" in message:
                        lines.append(self._format_key_value("Content", message["content"], 1))

                elif msg_type == "error":
                    lines.append(self._format_header("❌ Error", Colors.BRIGHT_RED))
                    lines.append("")
                    error_msg = message.get("error", message.get("message", "Unknown error"))
                    lines.append(self._color(self._indent_text(error_msg, 1), Colors.RED))

                else:
                    # Generic message type
                    lines.append(self._format_header(f"📨 {msg_type.title()}", Colors.BRIGHT_CYAN))
                    lines.append("")
                    for key, value in message.items():
                        if key != "type":
                            lines.append(self._format_key_value(key, value, 1))
            else:
                # Generic dict without type
                lines.append(self._format_header("📦 Message", Colors.BRIGHT_CYAN))
                lines.append("")
                for key, value in message.items():
                    lines.append(self._format_key_value(key, value, 1))

        elif isinstance(message, str):
            lines.append(self._format_header("💬 Message", Colors.BRIGHT_GREEN))
            lines.append("")
            lines.append(self._indent_text(message, 1))

        else:
            # Fallback for other types
            lines.append(self._format_header("📦 Message", Colors.BRIGHT_CYAN))
            lines.append("")
            lines.append(self._indent_text(str(message), 1))

        lines.append("")
        lines.append(self._format_footer())
        lines.append("")

        return "\n".join(lines)

    def _indent_text(self, text: str, indent_level: int) -> str:
        """Indent text with proper line wrapping"""
        indent_str = " " * (self.indent * indent_level)
        lines = text.split("\n")
        return "\n".join(f"{indent_str}{line}" for line in lines)

    def format_stream(self, message: Any) -> None:
        """
        Format and print a message (convenience method for streaming)

        Args:
            message: The message to format and print
        """
        print(self.format_message(message))


# Convenience function for quick formatting
def format_message(message: Any, use_colors: bool = True) -> str:
    """
    Quick format a message with default settings

    Args:
        message: The message to format
        use_colors: Whether to use ANSI colors

    Returns:
        Formatted string
    """
    formatter = MessageFormatter(use_colors=use_colors)
    return formatter.format_message(message)


# Convenience function for streaming
def print_formatted(message: Any, use_colors: bool = True) -> None:
    """
    Format and print a message in one call

    Args:
        message: The message to format and print
        use_colors: Whether to use ANSI colors
    """
    print(format_message(message, use_colors))


if __name__ == "__main__":
    # Demo usage
    formatter = MessageFormatter()

    # Example messages
    examples = [
        "Simple text message",
        {
            "type": "text",
            "content": "This is a text message from Claude agent"
        },
        {
            "type": "tool_use",
            "name": "Read",
            "input": {"file_path": "/path/to/file.py"}
        },
        {
            "type": "tool_result",
            "tool_use_id": "toolu_123",
            "content": "File contents here..."
        },
        {
            "type": "error",
            "error": "Something went wrong!"
        },
        {
            "custom_field": "value",
            "number": 42,
            "flag": True,
            "items": ["a", "b", "c"]
        }
    ]

    print(formatter._color("╔══════════════════════════════════════════════════════════════════════════════╗", Colors.BRIGHT_CYAN))
    print(formatter._color("║                    Claude Agent Message Formatter Demo                      ║", Colors.BRIGHT_CYAN))
    print(formatter._color("╚══════════════════════════════════════════════════════════════════════════════╝", Colors.BRIGHT_CYAN))
    print()

    for example in examples:
        formatter.format_stream(example)
