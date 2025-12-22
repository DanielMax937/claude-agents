import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher, AgentDefinition
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from message_formatter import MessageFormatter

load_dotenv()
project_root = str(Path.cwd().resolve())
formatter = MessageFormatter(use_colors=True)

# async def main():
#     async for message in query(
#         prompt="""tell me the weather about Hangzhou""",
#         options=ClaudeAgentOptions(allowed_tools=["Read", "Edit", "Write", "Bash", "WebSearch", "WebFetch"], cwd=project_root, system_prompt="You are a helpful assistant.")
#     ):
#         formatter.format_stream(message)

# async def log_file_change(input_data, tool_use_id, context):
#     file_path = input_data.get('tool_input', {}).get('file_path', 'unknown')
#     print(f"{datetime.now()}: modified {file_path}")
#     with open('./audit.log', 'a') as f:
#         f.write(f"{datetime.now()}: modified {file_path}\n")
#     return {}
#
# async def main():
#     async for message in query(
#         prompt="Refactor test_result_messages.py to improve readability",
#         options=ClaudeAgentOptions(
#             cwd=project_root,
#             system_prompt="You are a helpful assistant.",
#             permission_mode="acceptEdits",
#             hooks={
#                 "PostToolUse": [HookMatcher(matcher="Edit|Write", hooks=[log_file_change])]
#             }
#         )
#     ):
#         # if hasattr(message, "result"):
#         formatter.format_stream(message)

async def main():
    async for message in query(
        prompt="Use the code-reviewer agent to review this codebase",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Glob", "Grep", "Task"],
            agents={
                "code-reviewer": AgentDefinition(
                    description="Expert code reviewer for quality and security reviews.",
                    prompt="Analyze code quality and suggest improvements.",
                    tools=["Read", "Glob", "Grep"]
                )
            }
        )
    ):
        # if hasattr(message, "result"):
        formatter.format_stream(message)

asyncio.run(main())