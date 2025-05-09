#!/usr/bin/env python3
"""Generate trend bar chart for problem logstash documents per hour."""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import seaborn as sns

from platform_problem_monitoring_core.utils import load_json, logger


def _parse_hourly_data(hourly_data_file: str) -> Tuple[List[datetime], List[int]]:
    """
    Parse hourly data from JSON file.

    Args:
        hourly_data_file: Path to the hourly data JSON file

    Returns:
        Tuple of (timestamps, counts)

    Raises:
        FileNotFoundError: If the hourly data file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        KeyError: If required fields are missing in the JSON data
    """
    data = load_json(hourly_data_file)
    timestamps: List[datetime] = []
    counts: List[int] = []

    if not data:
        logger.warning("Hourly data file is empty or contains no valid entries")
        return timestamps, counts

    try:
        for entry in data:
            # Parse the end time as that represents the hour's data point
            # Handle both "Z" (UTC) suffix and +00:00 format
            end_time = entry.get("end_time", "")
            if not end_time:
                logger.warning(f"Skipping entry with missing end_time: {entry}")
                continue

            # Standardize date format
            end_time = end_time.replace("Z", "+00:00")
            timestamps.append(datetime.fromisoformat(end_time))

            # Get count, defaulting to 0 if missing
            count = entry.get("count", 0)
            counts.append(count)
    except (ValueError, TypeError) as e:
        logger.error(f"Error parsing hourly data: {e}")
        error_msg = f"Invalid date format in hourly data: {e}"
        raise ValueError(error_msg) from e

    return timestamps, counts


def _format_x_axis_labels(ax: plt.Axes, timestamps: List[datetime]) -> None:
    """
    Format x-axis labels for better readability.

    Args:
        ax: Matplotlib axes object
        timestamps: List of datetime objects
    """
    if not timestamps:
        logger.warning("No timestamps provided for axis formatting")
        return

    # Set major ticks at hour intervals
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

    # Rotate labels for better readability but provide more space
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor", fontsize=9)

    # Add extra space at the bottom to prevent labels from being cut off
    plt.gcf().subplots_adjust(bottom=0.15)

    # Add date labels directly to the main x-axis with more padding
    # Place them at the beginning, middle and end for better orientation
    # Convert datetime objects to matplotlib date numbers
    date_nums = mdates.date2num(timestamps)
    if len(timestamps) >= 3:
        middle_idx = len(timestamps) // 2
        ax.set_xticks([date_nums[0], date_nums[middle_idx], date_nums[-1]])
        ax.set_xticklabels(
            [t.strftime("%Y-%m-%d %H:%M") for t in [timestamps[0], timestamps[middle_idx], timestamps[-1]]], fontsize=8
        )
    else:
        ax.set_xticks([date_nums[0], date_nums[-1]])
        ax.set_xticklabels([t.strftime("%Y-%m-%d %H:%M") for t in [timestamps[0], timestamps[-1]]], fontsize=8)

    # Remove all spines from the axis
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Add a bit more padding at the bottom
    ax.tick_params(axis="x", which="major", pad=8)


def generate_trend_chart(hourly_data_file: str, output_image_file: str) -> None:
    """
    Generate trend bar chart for problem logstash documents per hour.

    Args:
        hourly_data_file: Path to the hourly data JSON file
        output_image_file: Path to store the generated chart image

    Raises:
        FileNotFoundError: If the hourly data file doesn't exist
        ValueError: If the data cannot be parsed correctly
        OSError: If the output image cannot be written
    """
    logger.info("Generating trend chart")
    logger.info(f"Hourly data file: {hourly_data_file}")
    logger.info(f"Output image file: {output_image_file}")

    # Parse the hourly data
    timestamps, counts = _parse_hourly_data(hourly_data_file)

    if not timestamps:
        logger.warning("No data points found in hourly data file")
        # Create a simple empty chart instead of failing
        fig, ax = plt.subplots(figsize=(11, 5))
        ax.text(0.5, 0.5, "No data available for the selected time period", ha="center", va="center", fontsize=12)
        ax.set_axis_off()
    else:
        logger.info(f"Parsed {len(timestamps)} data points")

        # Set up the style
        sns.set_style("whitegrid")
        sns.set_context("notebook", font_scale=1.1)

        # Create the figure and axis with white background - slightly larger size for more padding
        fig, ax = plt.subplots(figsize=(11, 5))
        fig.patch.set_facecolor("white")  # White background for the figure
        ax.patch.set_facecolor("white")  # White background for the axis

        # Add padding around the plot area
        plt.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.15)

        # Convert datetime objects to matplotlib date numbers
        date_nums = mdates.date2num(timestamps)

        # Plot the bars
        bars = ax.bar(date_nums, counts, width=0.02, color=sns.color_palette("deep")[0], alpha=0.7)

        # Customize the plot
        ax.set_title(" ", pad=20, fontsize=12, fontweight="bold")
        ax.set_ylabel("Number of Problems", fontsize=10, labelpad=10)  # Add padding to y-label

        # Add more space at the bottom and top of the y-axis
        y_min, y_max = ax.get_ylim()
        ax.set_ylim(0, y_max * 1.15)  # Add 15% more space at the top

        # Only show horizontal grid lines
        ax.grid(True, axis="y", linestyle="--", alpha=0.7)
        ax.grid(False, axis="x")

        # Format x-axis
        _format_x_axis_labels(ax, timestamps)

        # Add value labels on top of bars with more space
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + (y_max * 0.02),
                f"{int(height)}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

    # Ensure output directory exists
    output_path = Path(output_image_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Use tight_layout with padding parameter for more breathing space
    plt.tight_layout(pad=1.5)

    try:
        # Save the chart with a white background
        plt.savefig(
            output_image_file, dpi=300, bbox_inches="tight", facecolor="white", pad_inches=0.25
        )  # Add extra padding around the entire figure
        logger.info(f"Chart saved to {output_image_file}")
    except OSError as e:
        logger.error(f"Failed to save chart to {output_image_file}: {e}")
        raise
    finally:
        # Close the figure to free memory
        plt.close()


def main() -> None:
    """Execute the script when run directly."""
    parser = argparse.ArgumentParser(description="Generate trend bar chart for problem logstash documents per hour")
    parser.add_argument("--hourly-data-file", required=True, help="Path to the hourly data JSON file")
    parser.add_argument("--output-file", required=True, help="Path to store the generated chart image")

    args = parser.parse_args()

    try:
        generate_trend_chart(args.hourly_data_file, args.output_file)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error generating trend chart: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
