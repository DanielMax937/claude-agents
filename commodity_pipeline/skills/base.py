"""Base classes for skill wrappers."""
from abc import ABC, abstractmethod
from typing import Any
import sys
from pathlib import Path

# Add project root to path so we can import skill_wrapper
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from skill_wrapper import SkillWrapper, SkillOutputFormat, SkillResult


class SkillError(Exception):
    """Error raised when a skill execution fails."""

    def __init__(self, skill_name: str, message: str):
        self.skill_name = skill_name
        self.message = message
        super().__init__(f"Skill '{skill_name}' failed: {message}")


class BaseSkillWrapper(ABC):
    """Abstract base class for skill wrappers."""

    def __init__(self):
        """Initialize with a SkillWrapper instance."""
        self._wrapper = SkillWrapper()

    @property
    @abstractmethod
    def skill_name(self) -> str:
        """The name of the Claude Code skill."""
        pass

    def _run(self, script_name: str, args: str = "",
             output_format: SkillOutputFormat = SkillOutputFormat.JSON) -> SkillResult:
        """Run a skill script and return the result."""
        result = self._wrapper.run(self.skill_name, script_name, args=args,
                                   output_format=output_format)
        if not result.success:
            raise SkillError(self.skill_name, result.error or "Unknown error")
        return result

    @property
    def parsed_output(self) -> Any:
        """Alias for getting parsed output from last result."""
        return None  # Subclasses will implement as needed
