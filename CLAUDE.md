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

---

## Development Workflow (Superpowers)

**MANDATORY**: When adding new features, updating code, refactoring, or building something, you MUST follow this workflow. Do not skip steps.

### When to Use This Workflow

- Adding new features
- Updating existing functionality
- Refactoring code
- Building new components
- Fixing complex bugs
- Any non-trivial code changes

### Workflow Overview

```
1. BRAINSTORM → 2. SETUP WORKSPACE → 3. WRITE PLAN → 4. EXECUTE → 5. FINISH
```

### Phase 1: Brainstorming

**Invoke**: `/superpowers:brainstorm`

- Understand project context (files, docs, commits)
- Ask ONE question at a time (prefer multiple choice)
- Propose 2-3 approaches with trade-offs
- Present design in 200-300 word chunks for validation
- Output: `docs/plans/YYYY-MM-DD-<topic>-design.md`

### Phase 2: Setup Workspace

**Skill**: `using-git-worktrees`

- Create isolated git worktree on new branch
- Run project setup
- Verify clean test baseline

### Phase 3: Write Plan

**Invoke**: `/superpowers:write-plan`

- Break work into bite-sized tasks (2-5 min each)
- Each task has:
  - Exact file paths
  - Complete code (not "add validation")
  - Verification steps
- Output: `docs/plans/YYYY-MM-DD-<feature>.md`

### Phase 4: Execute Plan

Choose one execution mode:

#### Option A: Subagent-Driven (Recommended)

**Skill**: `subagent-driven-development`

Best for: Independent tasks, faster iteration, same session

```
FOR EACH TASK:
│
├─ 1. Dispatch Implementer Subagent
│     • Provide full task text + context
│     • Answer any questions
│
├─ 2. Implementer Does TDD
│     ┌─────┐   ┌─────┐   ┌─────────┐
│     │ RED │ → │GREEN│ → │REFACTOR │ → Commit
│     └─────┘   └─────┘   └─────────┘
│
│     ⚠️  CODE BEFORE TEST? DELETE IT.
│     ⚠️  TEST PASSES IMMEDIATELY? WRONG TEST.
│
├─ 3. Spec Review (spec-reviewer-prompt.md)
│     • Did we build what was asked?
│     • Nothing missing? Nothing extra?
│     • ❌ FAIL → Implementer fixes → Re-review
│
├─ 4. Code Quality Review (requesting-code-review)
│     • Critical → BLOCK, fix immediately
│     • Important → Fix before next task
│     • Minor → Note for later
│     • ❌ ISSUES → Implementer fixes → Re-review
│
└─ 5. Mark Complete → Next Task
```

#### Option B: Executing-Plans

**Skill**: `executing-plans`

Best for: Parallel sessions, more human oversight

```
FOR EACH BATCH (3 tasks):
│
├─ Task 1: TDD Cycle → Commit
├─ Task 2: TDD Cycle → Commit
├─ Task 3: TDD Cycle → Commit
│
└─ 🛑 HUMAN CHECKPOINT
     • Review batch results
     • Code review
     • Approve / Request changes
```

### Phase 5: Finish Branch

**Skill**: `finishing-a-development-branch`

- Final code review (entire implementation)
- Verify all tests pass
- Options: merge / PR / keep / discard
- Clean up worktree

### TDD: The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

**RED → GREEN → REFACTOR cycle**:

1. **RED**: Write failing test (one behavior, clear name)
2. **Verify RED**: Run test, MUST FAIL for expected reason
3. **GREEN**: Write minimal code to pass
4. **Verify GREEN**: Run test, MUST PASS (all tests green)
5. **REFACTOR**: Clean up (stay green)
6. **Commit**

**Red Flags (STOP and start over)**:
- Code written before test
- Test passes immediately
- "I'll add tests later"
- "This is too simple to test"

### Code Review Classification

| Level | Action |
|-------|--------|
| **Critical** | BLOCK - Fix before proceeding |
| **Important** | Fix before next task |
| **Minor** | Note for later |

### Quick Reference

| Phase | Command/Skill | Output |
|-------|---------------|--------|
| Brainstorm | `/superpowers:brainstorm` | design.md |
| Workspace | `using-git-worktrees` | New branch |
| Plan | `/superpowers:write-plan` | plan.md |
| Execute | `subagent-driven-development` or `executing-plans` | Code + Tests |
| Finish | `finishing-a-development-branch` | Merge/PR |
