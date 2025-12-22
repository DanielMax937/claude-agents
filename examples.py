"""
Example usage of the Claude Agent Message Formatter.

This module demonstrates various ways to use the MessageFormatter class
for formatting Claude Agent messages, including basic text, tool usage,
errors, and custom data structures.
"""

import time
from typing import Any, Dict, List

from message_formatter import MessageFormatter, format_message, print_formatted

# Display Constants
SEPARATOR_WIDTH = 80
SEPARATOR_CHAR = "="
BANNER_WIDTH = 78
BANNER_PADDING_LEFT = 12
BANNER_PADDING_RIGHT = 19

# Timing Constants
SLEEP_DURATION = 0.5
STREAMING_DELAY = 0.3


# ============================================================================
# Helper Functions
# ============================================================================

def print_example_header(example_num: int, title: str) -> None:
    """Print a formatted header for an example section."""
    separator = SEPARATOR_CHAR * SEPARATOR_WIDTH
    print(f"\n{separator}")
    print(f"EXAMPLE {example_num}: {title}")
    print(separator)


# ============================================================================
# Example Functions
# ============================================================================

def example_basic() -> None:
    """Demonstrate basic message formatting with simple strings and structured text."""
    print_example_header(1, "Basic Usage")

    formatter = MessageFormatter()

    # Simple string message
    formatter.format_stream("Hello from Claude Agent!")
    time.sleep(SLEEP_DURATION)

    # Structured text message
    formatter.format_stream({
        "type": "text",
        "content": "This is a formatted text message with proper structure."
    })


def example_tool_messages() -> None:
    """Demonstrate tool invocation and result message formatting."""
    print_example_header(2, "Tool Messages")

    formatter = MessageFormatter()

    # Tool invocation message
    formatter.format_stream({
        "type": "tool_use",
        "name": "Read",
        "input": {
            "file_path": "/Users/daniel/Desktop/git/claude-kit/main.py",
            "offset": 0,
            "limit": 100
        }
    })
    time.sleep(SLEEP_DURATION)

    # Tool result message
    formatter.format_stream({
        "type": "tool_result",
        "tool_use_id": "toolu_abc123",
        "content": "Successfully read 21 lines from the file."
    })


def example_errors() -> None:
    """Demonstrate error message formatting."""
    print_example_header(3, "Error Messages")

    formatter = MessageFormatter()

    formatter.format_stream({
        "type": "error",
        "error": "File not found: /path/to/nonexistent/file.py"
    })


def example_custom_data() -> None:
    """Demonstrate formatting of arbitrary nested data structures."""
    print_example_header(4, "Custom Data Structures")

    formatter = MessageFormatter()

    formatter.format_stream({
        "user": "developer",
        "timestamp": "2025-12-22T15:53:51",
        "status": "active",
        "tokens_used": 1500,
        "tools_available": ["Read", "Write", "Edit", "Bash"],
        "config": {
            "model": "claude-3-5-sonnet",
            "temperature": 0.7
        }
    })


def example_quick_functions() -> None:
    """Demonstrate convenience functions for simple formatting without creating instances."""
    print_example_header(5, "Quick Functions")

    # Direct print with formatting
    print_formatted("Quick formatted message!")
    time.sleep(SLEEP_DURATION)

    # Get formatted string without printing
    formatted_str = format_message({
        "type": "tool_use",
        "name": "Bash",
        "input": {"command": "ls -la"}
    })
    print(formatted_str)


def example_no_colors() -> None:
    """Demonstrate formatting without colors for log files or unsupported environments."""
    print_example_header(6, "No Colors (for logs)")

    formatter = MessageFormatter(use_colors=False)

    formatter.format_stream({
        "type": "text",
        "content": "This message has no colors - suitable for log files."
    })


def example_streaming_simulation() -> None:
    """Simulate a realistic agent workflow with sequential tool invocations."""
    print_example_header(7, "Simulated Agent Stream")

    formatter = MessageFormatter()

    # Define a realistic agent interaction workflow
    messages: List[Dict[str, Any]] = [
        {"type": "text", "content": "Starting task: Read and analyze files"},
        {"type": "tool_use", "name": "Bash", "input": {"command": "ls -la"}},
        {"type": "tool_result", "tool_use_id": "tool_1", "content": "total 288\ndrwxr-xr-x 12 files..."},
        {"type": "tool_use", "name": "Read", "input": {"file_path": "/path/to/file.py"}},
        {"type": "tool_result", "tool_use_id": "tool_2", "content": "import asyncio\nfrom claude..."},
        {"type": "text", "content": "Analysis complete! Found 3 Python files and 2 configuration files."},
    ]

    for message in messages:
        formatter.format_stream(message)
        time.sleep(STREAMING_DELAY)

# ============================================================================
# Main Execution
# ============================================================================

def print_banner() -> None:
    """Print the welcome banner for the examples."""
    banner_title = "Claude Agent Message Formatter - Usage Examples"

    print("\n")
    print("╔" + "═" * BANNER_WIDTH + "╗")
    print("║" + " " * BANNER_PADDING_LEFT + banner_title + " " * BANNER_PADDING_RIGHT + "║")
    print("╚" + "═" * BANNER_WIDTH + "╝")


def print_completion_message() -> None:
    """Print the completion message after all examples."""
    separator = SEPARATOR_CHAR * SEPARATOR_WIDTH
    print(f"\n{separator}")
    print("All examples completed!")
    print(f"{separator}\n")


def run_all_examples() -> None:
    """Execute all example functions in sequence."""
    example_basic()
    example_tool_messages()
    example_errors()
    example_custom_data()
    example_quick_functions()
    example_no_colors()
    example_streaming_simulation()


if __name__ == "__main__":
    print_banner()
    run_all_examples()
    print_completion_message()
