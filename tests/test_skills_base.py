"""Tests for skill wrapper base."""
import pytest


def test_skill_error_creation():
    """SkillError should store skill name and error message."""
    from commodity_pipeline.skills.base import SkillError

    err = SkillError("china-futures", "Network timeout")

    assert err.skill_name == "china-futures"
    assert err.message == "Network timeout"
    assert "china-futures" in str(err)
    assert "Network timeout" in str(err)


def test_base_skill_wrapper_abstract():
    """BaseSkillWrapper should be abstract and require skill_name."""
    from commodity_pipeline.skills.base import BaseSkillWrapper

    # Should not be instantiable directly
    with pytest.raises(TypeError):
        BaseSkillWrapper()
