"""
Skill Wrapper - Programmatically invoke Claude Code skills from Python

This module provides a unified interface to call skill scripts, handling
argument passing, subprocess execution, and output formatting.
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from enum import Enum


class SkillOutputFormat(Enum):
    """Output format options for skill execution"""
    RAW = "raw"  # Raw string output
    JSON = "json"  # Parse as JSON
    LINES = "lines"  # Split into lines
    AUTO = "auto"  # Auto-detect format


@dataclass
class SkillResult:
    """Result from skill execution"""
    success: bool
    output: Any
    error: Optional[str] = None
    returncode: int = 0
    skill_name: str = ""
    script_name: str = ""

    def __repr__(self):
        status = "✓" if self.success else "✗"
        return f"SkillResult({status} {self.skill_name}:{self.script_name})"


class SkillWrapper:
    """
    Wrapper for executing Claude Code skill scripts programmatically.

    Skills are located in ~/.claude/skills/ directory, with each skill
    containing a scripts/ subdirectory with Python executables.

    Example:
        >>> wrapper = SkillWrapper()
        >>> result = wrapper.run("options", "pricing", args="--underlying 100 --strike 105")
        >>> print(result.output)
    """

    def __init__(self, skills_dir: Optional[Path] = None):
        """
        Initialize the skill wrapper.

        Args:
            skills_dir: Custom skills directory path. Defaults to ~/.claude/skills/
        """
        self.skills_dir = skills_dir or Path.home() / ".claude" / "skills"
        if not self.skills_dir.exists():
            raise FileNotFoundError(f"Skills directory not found: {self.skills_dir}")

    def list_skills(self) -> List[str]:
        """
        List all available skills.

        Returns:
            List of skill names
        """
        skills = []
        for item in self.skills_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                skill_md = item / "SKILL.md"
                if skill_md.exists():
                    skills.append(item.name)
        return sorted(skills)

    def list_scripts(self, skill_name: str) -> List[str]:
        """
        List all scripts in a skill.

        Args:
            skill_name: Name of the skill

        Returns:
            List of script names (without .py extension)
        """
        scripts_dir = self.skills_dir / skill_name / "scripts"
        if not scripts_dir.exists():
            return []

        scripts = []
        for script_file in scripts_dir.glob("*.py"):
            if not script_file.name.startswith('_'):
                scripts.append(script_file.stem)
        return sorted(scripts)

    def get_skill_path(self, skill_name: str) -> Path:
        """Get the path to a skill directory."""
        skill_path = self.skills_dir / skill_name
        if not skill_path.exists():
            raise FileNotFoundError(f"Skill not found: {skill_name}")
        return skill_path

    def get_script_path(self, skill_name: str, script_name: str) -> Path:
        """Get the path to a specific script within a skill."""
        script_path = self.skills_dir / skill_name / "scripts" / f"{script_name}.py"
        if not script_path.exists():
            raise FileNotFoundError(
                f"Script '{script_name}' not found in skill '{skill_name}'"
            )
        return script_path

    def run(
        self,
        skill_name: str,
        script_name: str,
        args: Optional[Union[str, List[str]]] = None,
        output_format: SkillOutputFormat = SkillOutputFormat.RAW,
        timeout: Optional[int] = 30,
        env: Optional[Dict[str, str]] = None,
        capture_stderr: bool = True,
    ) -> SkillResult:
        """
        Execute a skill script.

        Args:
            skill_name: Name of the skill (e.g., "options", "weather")
            script_name: Name of the script without .py (e.g., "pricing", "greeks")
            args: Command-line arguments as string or list
            output_format: How to format the output (RAW, JSON, LINES, AUTO)
            timeout: Execution timeout in seconds (None for no timeout)
            env: Additional environment variables
            capture_stderr: Whether to capture stderr

        Returns:
            SkillResult with execution results

        Example:
            >>> result = wrapper.run("options", "pricing",
            ...                      args="--underlying 100 --strike 105 --rate 0.05")
            >>> if result.success:
            ...     print(result.output)
        """
        try:
            script_path = self.get_script_path(skill_name, script_name)

            # Build command
            cmd = [sys.executable, str(script_path)]

            # Add arguments
            if args:
                if isinstance(args, str):
                    # Split string arguments (simple split, doesn't handle quotes)
                    cmd.extend(args.split())
                else:
                    cmd.extend(args)

            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**subprocess.os.environ, **(env or {})}
            )

            # Process output
            stdout = result.stdout
            stderr = result.stderr if capture_stderr else None

            # Format output based on requested format
            output = self._format_output(stdout, output_format)

            # Determine success
            success = result.returncode == 0
            error = stderr if not success and stderr else None

            return SkillResult(
                success=success,
                output=output,
                error=error,
                returncode=result.returncode,
                skill_name=skill_name,
                script_name=script_name,
            )

        except subprocess.TimeoutExpired:
            return SkillResult(
                success=False,
                output=None,
                error=f"Script execution timed out after {timeout} seconds",
                returncode=-1,
                skill_name=skill_name,
                script_name=script_name,
            )
        except FileNotFoundError as e:
            return SkillResult(
                success=False,
                output=None,
                error=str(e),
                returncode=-1,
                skill_name=skill_name,
                script_name=script_name,
            )
        except Exception as e:
            return SkillResult(
                success=False,
                output=None,
                error=f"Unexpected error: {str(e)}",
                returncode=-1,
                skill_name=skill_name,
                script_name=script_name,
            )

    def _format_output(self, stdout: str, format_type: SkillOutputFormat) -> Any:
        """Format output according to the specified format type."""
        if not stdout:
            return None

        if format_type == SkillOutputFormat.RAW:
            return stdout

        elif format_type == SkillOutputFormat.LINES:
            return [line for line in stdout.split('\n') if line.strip()]

        elif format_type == SkillOutputFormat.JSON:
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:
                return stdout

        elif format_type == SkillOutputFormat.AUTO:
            # Try JSON first
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:
                # If it has multiple lines, return as lines
                lines = [line for line in stdout.split('\n') if line.strip()]
                if len(lines) > 1:
                    return lines
                # Otherwise return raw
                return stdout

        return stdout

    def run_pipeline(
        self,
        commands: List[Dict[str, Any]],
        stop_on_error: bool = True,
    ) -> List[SkillResult]:
        """
        Run multiple skill commands in sequence.

        Args:
            commands: List of command dicts with keys: skill_name, script_name, args
            stop_on_error: Whether to stop execution if any command fails

        Returns:
            List of SkillResults

        Example:
            >>> results = wrapper.run_pipeline([
            ...     {"skill_name": "options", "script_name": "pricing", "args": "--strike 100"},
            ...     {"skill_name": "options", "script_name": "greeks", "args": "--strike 100"},
            ... ])
        """
        results = []
        for cmd in commands:
            result = self.run(**cmd)
            results.append(result)
            if not result.success and stop_on_error:
                break
        return results


# Convenience functions
def run_skill(
    skill_name: str,
    script_name: str,
    args: Optional[Union[str, List[str]]] = None,
    **kwargs
) -> SkillResult:
    """
    Convenience function to run a skill script.

    Args:
        skill_name: Name of the skill
        script_name: Name of the script
        args: Arguments to pass
        **kwargs: Additional arguments to pass to SkillWrapper.run()

    Returns:
        SkillResult

    Example:
        >>> result = run_skill("options", "pricing", "--underlying 100 --strike 105")
        >>> print(result.output)
    """
    wrapper = SkillWrapper()
    return wrapper.run(skill_name, script_name, args, **kwargs)


def list_available_skills() -> List[str]:
    """List all available skills."""
    wrapper = SkillWrapper()
    return wrapper.list_skills()


if __name__ == "__main__":
    # Demo usage
    wrapper = SkillWrapper()

    print("Available skills:")
    for skill in wrapper.list_skills():
        scripts = wrapper.list_scripts(skill)
        print(f"  {skill}: {', '.join(scripts)}")
