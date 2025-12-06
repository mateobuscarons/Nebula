#!/usr/bin/env python3
"""Main entry point for the Guided Learning System."""

import sys
import argparse
import logging
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.table import Table

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.logging_config import setup_logging
from core.lesson_loader import LessonLoader
from cli.interface import create_cli


logger = logging.getLogger(__name__)
console = Console()


def find_lesson_plan_files() -> list:
    """Find all LessonPlan*.json files in parent directory."""
    parent_dir = Path(__file__).parent.parent
    lesson_files = sorted(parent_dir.glob("LessonPlan*.json"))
    return [str(f) for f in lesson_files]


def interactive_file_selection() -> str:
    """Interactively select a lesson plan file."""
    lesson_files = find_lesson_plan_files()

    if not lesson_files:
        console.print("[red]No LessonPlan*.json files found in parent directory.[/red]")
        sys.exit(1)

    if len(lesson_files) == 1:
        console.print(f"[green]Found lesson plan:[/green] {Path(lesson_files[0]).name}")
        return lesson_files[0]

    # Display available files
    table = Table(title="Available Lesson Plans", show_header=True, header_style="bold magenta")
    table.add_column("#", style="cyan", width=4)
    table.add_column("File Name", style="green")

    for i, file_path in enumerate(lesson_files, 1):
        table.add_row(str(i), Path(file_path).name)

    console.print()
    console.print(table)
    console.print()

    choice = IntPrompt.ask(
        "[bold]Select a lesson plan[/bold]",
        choices=[str(i) for i in range(1, len(lesson_files) + 1)]
    )

    return lesson_files[int(choice) - 1]


def interactive_lesson_selection(lesson_file: str) -> int:
    """Interactively select a lesson from the plan."""
    try:
        lessons = LessonLoader.list_lessons(lesson_file)
    except Exception as e:
        console.print(f"[red]Error loading lessons: {e}[/red]")
        sys.exit(1)

    if not lessons:
        console.print("[red]No lessons found in the lesson plan.[/red]")
        sys.exit(1)

    if len(lessons) == 1:
        console.print(f"[green]Starting lesson:[/green] {lessons[0]['title']}")
        return 1

    # Display available lessons
    table = Table(title="Available Lessons", show_header=True, header_style="bold magenta")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Lesson Title", style="green")
    table.add_column("Topics", style="white")

    for lesson in lessons:
        topics = ", ".join(lesson['topics']) if lesson['topics'] else "N/A"
        table.add_row(
            str(lesson['number']),
            lesson['title'],
            topics[:60] + "..." if len(topics) > 60 else topics
        )

    console.print()
    console.print(table)
    console.print()

    choice = IntPrompt.ask(
        "[bold]Select a lesson[/bold]",
        choices=[str(lesson['number']) for lesson in lessons]
    )

    return int(choice)


def main():
    """Main function to run the Guided Learning System."""
    parser = argparse.ArgumentParser(
        description="Guided Learning System - Multi-Agent Educational Platform"
    )
    parser.add_argument(
        "lesson_file",
        type=str,
        nargs="?",  # Make it optional
        help="Path to the lesson plan JSON file (optional - will prompt if not provided)"
    )
    parser.add_argument(
        "--lesson-number",
        type=int,
        default=None,
        help="Which lesson to load from the plan (will prompt if not provided)"
    )
    parser.add_argument(
        "--list-lessons",
        action="store_true",
        help="List all lessons in the file and exit"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="DEBUG",
        help="Logging level (default: DEBUG)"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="guided_learning.log",
        help="Log file path (default: guided_learning.log)"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(log_file=args.log_file, log_level=args.log_level)

    logger.info("Starting Guided Learning System")

    # Interactive mode: select file if not provided
    lesson_file = args.lesson_file
    if not lesson_file:
        console.print("\n[bold cyan]Welcome to the Guided Learning System![/bold cyan]\n")
        lesson_file = interactive_file_selection()

    logger.info(f"Lesson file: {lesson_file}")

    try:
        # List lessons mode
        if args.list_lessons:
            lessons = LessonLoader.list_lessons(lesson_file)
            print("\nAvailable Lessons:")
            print("-" * 60)
            for lesson in lessons:
                print(f"{lesson['number']}. {lesson['title']}")
                print(f"   Topics: {', '.join(lesson['topics'])}")
                print()
            return

        # Interactive mode: select lesson if not provided
        lesson_number = args.lesson_number
        if lesson_number is None:
            lesson_number = interactive_lesson_selection(lesson_file)

        # Load the lesson
        lesson_context = LessonLoader.load_lesson(
            lesson_file,
            lesson_number
        )

        logger.info(f"Loaded lesson: {lesson_context.title}")

        # Create and start CLI
        cli = create_cli()
        cli.start_session(lesson_context)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"\nError: {e}")
        print("Please check the file path and try again.")
        sys.exit(1)

    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        print(f"\nError: {e}")
        sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Session interrupted by user")
        print("\n\nSession interrupted. Goodbye!")
        sys.exit(0)

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"\nUnexpected error: {e}")
        print("Check the log file for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
