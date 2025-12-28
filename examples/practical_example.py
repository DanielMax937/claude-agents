"""
Practical Example: Using skill_wrapper in a real workflow

This example shows how to integrate skill_wrapper into your
Claude-kit project to call skills programmatically.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from skill_wrapper import SkillWrapper, SkillOutputFormat, run_skill
from message_formatter import MessageFormatter, print_formatted


def analyze_option_strategy():
    """
    Example: Analyze an option strategy using the options skill
    """
    print("\n" + "=" * 60)
    print("Option Strategy Analysis Example")
    print("=" * 60 + "\n")

    # Define strategy parameters
    underlying_price = 100
    strike_price = 105
    time_to_expiry = 1.0  # 1 year
    risk_free_rate = 0.05
    volatility = 0.2

    # 1. Calculate option pricing
    print("1. Calculating option price...")
    pricing_result = run_skill(
        "options",
        "pricing",
        args=f"--spot {underlying_price} --strike {strike_price} "
             f"--time {time_to_expiry} --rate {risk_free_rate} "
             f"--vol {volatility} --type call"
    )

    if pricing_result.success:
        print(f"   ✓ Call Option Price:")
        print(f"   {pricing_result.output}")
    else:
        print(f"   ✗ Error: {pricing_result.error}")
        return

    # 2. Calculate Greeks
    print("\n2. Calculating Greeks...")
    greeks_result = run_skill(
        "options",
        "greeks",
        args=f"--spot {underlying_price} --strike {strike_price} "
             f"--time {time_to_expiry} --rate {risk_free_rate} "
             f"--vol {volatility} --type call"
    )

    if greeks_result.success:
        print(f"   ✓ Option Greeks:")
        print(f"   {greeks_result.output}")
    else:
        print(f"   ✗ Error: {greeks_result.error}")

    # 3. Analyze strategy payoff
    print("\n3. Analyzing long call strategy...")
    strategy_result = run_skill(
        "options",
        "strategies",
        args=f"long_call --strike {strike_price}"
    )

    if strategy_result.success:
        print(f"   ✓ Strategy Analysis:")
        print(f"   {strategy_result.output}")
    else:
        print(f"   ✗ Error: {strategy_result.error}")

    print("\n" + "=" * 60)


def fetch_market_data():
    """
    Example: Fetch Chinese futures data
    """
    print("\n" + "=" * 60)
    print("Market Data Fetching Example")
    print("=" * 60 + "\n")

    # Fetch futures data
    result = run_skill(
        "china-futures",
        "fetch_futures",
        args="--symbol cu --exchange SHFE"
    )

    if result.success:
        print("✓ Futures data fetched successfully")
        print(result.output)
    else:
        print(f"✗ Error: {result.error}")

    print("\n" + "=" * 60)


def technical_analysis_workflow():
    """
    Example: Run technical analysis on stock data
    """
    print("\n" + "=" * 60)
    print("Technical Analysis Workflow")
    print("=" * 60 + "\n")

    # Example: Analyze a stock with technical indicators
    result = run_skill(
        "technical-analysis",
        "analyze",
        args="--symbol AAPL --period 60d --indicators MACD,RSI,BOLL"
    )

    if result.success:
        print("✓ Technical analysis completed")
        print(result.output)
    else:
        print(f"✗ Error: {result.error}")

    print("\n" + "=" * 60)


def batch_processing_example():
    """
    Example: Process multiple symbols using pipeline
    """
    print("\n" + "=" * 60)
    print("Batch Processing Example")
    print("=" * 60 + "\n")

    wrapper = SkillWrapper()

    symbols = ["AAPL", "GOOGL", "MSFT"]

    for symbol in symbols:
        print(f"\nProcessing {symbol}...")

        # Create a pipeline for each symbol
        commands = [
            {
                "skill_name": "technical-analysis",
                "script_name": "indicators",
                "args": f"--symbol {symbol} --indicator RSI"
            },
            {
                "skill_name": "technical-analysis",
                "script_name": "indicators",
                "args": f"--symbol {symbol} --indicator MACD"
            },
        ]

        results = wrapper.run_pipeline(commands, stop_on_error=False)

        for result in results:
            if result.success:
                print(f"  ✓ {result.script_name}: OK")
            else:
                print(f"  ✗ {result.script_name}: {result.error}")

    print("\n" + "=" * 60)


def integrated_example():
    """
    Example: Integration with message_formatter for beautiful output
    """
    print("\n" + "=" * 60)
    print("Integrated Example with Message Formatting")
    print("=" * 60 + "\n")

    formatter = MessageFormatter(use_colors=True)

    # Run skill and format output
    result = run_skill(
        "options",
        "pricing",
        args="--spot 100 --strike 105 --time 1 --rate 0.05 --vol 0.2",
        output_format=SkillOutputFormat.AUTO
    )

    if result.success:
        # Format the output nicely
        print(formatter.colors.header("📊 Option Pricing Result"))
        print(formatter.colors.green("✓ Calculation successful\n"))
        print(formatter.colors.text(result.output))
    else:
        print(formatter.colors.header("❌ Error"))
        print(formatter.colors.error(result.error))

    print("\n" + "=" * 60)


def main():
    """Run practical examples"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 12 + "PRACTICAL SKILL WRAPPER EXAMPLES" + " " * 14 + "║")
    print("╚" + "═" * 58 + "╝")

    # Run the examples you want to test
    # Uncomment the ones that match your installed skills

    analyze_option_strategy()
    # fetch_market_data()  # Uncomment if you have china-futures skill
    # technical_analysis_workflow()  # Uncomment if you have technical-analysis skill
    # batch_processing_example()
    integrated_example()

    print("\n✨ All examples completed!\n")


if __name__ == "__main__":
    main()
