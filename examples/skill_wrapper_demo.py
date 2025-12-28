"""
Skill Wrapper Demo - Examples of using the skill wrapper

This script demonstrates different ways to use the skill wrapper
to programmatically call Claude Code skills from Python.
"""

import sys
from pathlib import Path

# Add parent directory to path to import skill_wrapper
sys.path.insert(0, str(Path(__file__).parent.parent))

from skill_wrapper import (
    SkillWrapper,
    SkillOutputFormat,
    run_skill,
    list_available_skills
)


def demo_basic_usage():
    """Demonstrate basic skill execution"""
    print("=" * 60)
    print("DEMO 1: Basic Usage")
    print("=" * 60)

    # Initialize wrapper
    wrapper = SkillWrapper()

    # List all available skills
    print("\nAvailable skills:")
    skills = wrapper.list_skills()
    for skill in skills:
        print(f"  - {skill}")

    print("\n" + "-" * 60)


def demo_options_skill():
    """Demonstrate options skill usage"""
    print("\n" + "=" * 60)
    print("DEMO 2: Options Skill - Black-Scholes Pricing")
    print("=" * 60)

    # Example: Call options pricing script
    result = run_skill(
        skill_name="options",
        script_name="pricing",
        args="--spot 100 --strike 105 --time 1 --rate 0.05 --vol 0.2 --type call"
    )

    print(f"\nResult: {result}")
    print(f"Success: {result.success}")
    print(f"Output:\n{result.output}")

    if not result.success:
        print(f"Error: {result.error}")

    print("\n" + "-" * 60)


def demo_weather_skill():
    """Demonstrate weather skill usage"""
    print("\n" + "=" * 60)
    print("DEMO 3: Weather Skill")
    print("=" * 60)

    result = run_skill(
        skill_name="weather",
        script_name="get_weather",
        args="--location 'San Francisco'"
    )

    print(f"\nResult: {result}")
    print(f"Output:\n{result.output}")

    print("\n" + "-" * 60)


def demo_output_formats():
    """Demonstrate different output format options"""
    print("\n" + "=" * 60)
    print("DEMO 4: Output Format Options")
    print("=" * 60)

    wrapper = SkillWrapper()

    # RAW format (default)
    print("\n1. RAW format:")
    result = wrapper.run(
        "options",
        "pricing",
        args="--spot 100 --strike 100 --time 1 --rate 0.05 --vol 0.2",
        output_format=SkillOutputFormat.RAW
    )
    print(f"Type: {type(result.output)}")
    print(f"Output: {result.output[:100]}...")

    # JSON format
    print("\n2. JSON format (if applicable):")
    result = wrapper.run(
        "options",
        "pricing",
        args="--spot 100 --strike 100 --time 1 --rate 0.05 --vol 0.2 --json",
        output_format=SkillOutputFormat.JSON
    )
    print(f"Type: {type(result.output)}")
    print(f"Output: {result.output}")

    # LINES format
    print("\n3. LINES format:")
    result = wrapper.run(
        "options",
        "greeks",
        args="--spot 100 --strike 100 --time 1 --rate 0.05 --vol 0.2",
        output_format=SkillOutputFormat.LINES
    )
    print(f"Type: {type(result.output)}")
    print(f"Lines: {len(result.output) if result.output else 0}")

    # AUTO format
    print("\n4. AUTO format:")
    result = wrapper.run(
        "options",
        "pricing",
        args="--spot 100 --strike 100 --time 1 --rate 0.05 --vol 0.2",
        output_format=SkillOutputFormat.AUTO
    )
    print(f"Type: {type(result.output)}")
    print(f"Auto-detected format: {result.output}")

    print("\n" + "-" * 60)


def demo_pipeline():
    """Demonstrate running multiple skills in sequence"""
    print("\n" + "=" * 60)
    print("DEMO 5: Pipeline - Multiple Skills in Sequence")
    print("=" * 60)

    wrapper = SkillWrapper()

    # Run multiple commands in sequence
    commands = [
        {
            "skill_name": "options",
            "script_name": "pricing",
            "args": "--spot 100 --strike 105 --time 1 --rate 0.05 --vol 0.2"
        },
        {
            "skill_name": "options",
            "script_name": "greeks",
            "args": "--spot 100 --strike 105 --time 1 --rate 0.05 --vol 0.2"
        },
        {
            "skill_name": "options",
            "script_name": "strategies",
            "args": "long_call --strike 105"
        },
    ]

    results = wrapper.run_pipeline(commands, stop_on_error=True)

    for i, result in enumerate(results, 1):
        print(f"\nCommand {i}: {result.skill_name}:{result.script_name}")
        print(f"Success: {result.success}")
        if result.success:
            print(f"Output: {result.output[:200]}...")
        else:
            print(f"Error: {result.error}")

    print("\n" + "-" * 60)


def demo_error_handling():
    """Demonstrate error handling"""
    print("\n" + "=" * 60)
    print("DEMO 6: Error Handling")
    print("=" * 60)

    # Try to run a non-existent skill
    print("\n1. Non-existent skill:")
    result = run_skill("nonexistent", "script", args="--test")
    print(f"Success: {result.success}")
    print(f"Error: {result.error}")

    # Try to run a non-existent script
    print("\n2. Non-existent script:")
    result = run_skill("options", "nonexistent", args="--test")
    print(f"Success: {result.success}")
    print(f"Error: {result.error}")

    # Try with invalid arguments
    print("\n3. Invalid arguments (if handled by script):")
    result = run_skill("options", "pricing", args="--invalid-arg")
    print(f"Success: {result.success}")
    if not result.success:
        print(f"Error output: {result.error}")

    print("\n" + "-" * 60)


def demo_advanced_features():
    """Demonstrate advanced features"""
    print("\n" + "=" * 60)
    print("DEMO 7: Advanced Features")
    print("=" * 60)

    wrapper = SkillWrapper()

    # List scripts in a specific skill
    print("\n1. List scripts in 'options' skill:")
    scripts = wrapper.list_scripts("options")
    for script in scripts:
        print(f"  - {script}")

    # Custom timeout
    print("\n2. Custom timeout (2 seconds):")
    result = wrapper.run(
        "options",
        "pricing",
        args="--spot 100 --strike 100 --time 1 --rate 0.05 --vol 0.2",
        timeout=2
    )
    print(f"Success: {result.success}")
    print(f"Completed within timeout")

    # Environment variables
    print("\n3. Custom environment variables:")
    result = wrapper.run(
        "options",
        "pricing",
        args="--spot 100 --strike 100 --time 1 --rate 0.05 --vol 0.2",
        env={"DEBUG": "1"}
    )
    print(f"Success: {result.success}")

    print("\n" + "-" * 60)


def main():
    """Run all demos"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "SKILL WRAPPER DEMO" + " " * 25 + "║")
    print("╚" + "═" * 58 + "╝")

    try:
        # Run each demo
        demo_basic_usage()
        demo_options_skill()
        # demo_weather_skill()  # Uncomment if weather skill is configured
        demo_output_formats()
        demo_pipeline()
        demo_error_handling()
        demo_advanced_features()

        print("\n" + "=" * 60)
        print("All demos completed!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
