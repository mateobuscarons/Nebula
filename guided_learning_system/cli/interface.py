"""CLI interface for the Guided Learning System."""

import logging
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.table import Table
from rich.markdown import Markdown
from rich import print as rprint

from core import SessionState, LessonContext
from core.orchestrator import OrchestrationEngine


logger = logging.getLogger(__name__)


class CLI:
    """Command-line interface for interacting with the learning system."""

    def __init__(self):
        """Initialize the CLI."""
        self.console = Console()
        self.engine = OrchestrationEngine()
        self.state: Optional[SessionState] = None

        logger.info("CLI initialized")

    def start_session(self, lesson_context: LessonContext):
        """
        Start a new learning session.

        Args:
            lesson_context: The lesson to teach
        """
        self.console.clear()
        self._print_header()

        # Create session state
        self.state = SessionState.create_new(lesson_context)

        self.console.print(f"\n[bold blue]Starting Lesson:[/bold blue] {lesson_context.title}\n")

        # Generate paths
        with self.console.status("[bold green]Generating diverse learning paths..."):
            path_options = self.engine.initialize_session(self.state)

        # Display path options
        self._display_path_options(path_options)

        # User selects path
        path_id = self._select_path(path_options)
        self.engine.select_path(self.state, path_id)

        self.console.print(f"\n[green]✓[/green] Path selected: {self.state.teaching_path.name}\n")

        # Start teaching
        self._teaching_loop()

    def _teaching_loop(self):
        """Main teaching interaction loop."""
        # First tutor output (no evaluation)
        with self.console.status("[bold green]Preparing first teaching segment..."):
            first_output = self.engine.start_teaching(self.state)

        self._display_tutor_message(first_output)

        # Main loop
        while True:
            # Get user response
            user_input = self._get_user_input()

            if user_input.lower() in ['quit', 'exit', 'q']:
                self.console.print("\n[yellow]Session ended by user.[/yellow]")
                break

            # Process response
            with self.console.status("[bold green]Evaluating your response..."):
                next_output = self.engine.process_user_response(self.state, user_input)

            if next_output is None:
                # Lesson complete
                self._display_completion()
                break

            # Display next tutor message
            self._display_tutor_message(next_output)

    def _print_header(self):
        """Print the CLI header."""
        header = """
╔═══════════════════════════════════════════════════════════╗
║     Guided Learning System - Multi-Agent Architecture     ║
╚═══════════════════════════════════════════════════════════╝
        """
        self.console.print(header, style="bold cyan")

    def _display_path_options(self, path_options: list):
        """Display available teaching paths with their sequences."""
        self.console.print("\n[bold magenta]Available Learning Paths:[/bold magenta]\n")

        for i, option in enumerate(path_options, 1):
            # Path header
            self.console.print(f"[bold cyan]{option['id']}. {option['name']}[/bold cyan]")
            self.console.print(f"[dim]{option['description']}[/dim]")
            self.console.print(f"[yellow]({option['node_count']} nodes)[/yellow]\n")

            # Display sequence
            sequence = option.get('sequence', [])
            for j, node in enumerate(sequence, 1):
                arrow = "→" if j < len(sequence) else "✓"
                self.console.print(f"  {j}. {node['concept']}")
                self.console.print(f"     [dim]{node['goal']}[/dim]")
                if j < len(sequence):
                    self.console.print(f"     [dim]{arrow}[/dim]")

            self.console.print()  # Extra spacing between paths

    def _select_path(self, path_options: list) -> str:
        """Prompt user to select a path."""
        valid_ids = [opt["id"] for opt in path_options]

        while True:
            path_id = Prompt.ask("\n[bold]Select a path[/bold] (enter ID)", choices=valid_ids)
            return path_id

    def _display_tutor_message(self, message: str):
        """Display a tutor message in a styled panel."""
        self.console.print()
        panel = Panel(
            message,
            title="[bold blue]🎓 Tutor[/bold blue]",
            border_style="blue",
            padding=(1, 2)
        )
        self.console.print(panel)

    def _get_user_input(self) -> str:
        """Get user input with styled prompt."""
        self.console.print()
        user_input = Prompt.ask("[bold green]Your response[/bold green]")
        return user_input

    def _display_completion(self):
        """Display lesson completion message."""
        completion_msg = """
[bold green]🎉 Congratulations![/bold green]

You've completed this lesson! You've demonstrated understanding of all the core concepts.

[italic]Great work on your learning journey![/italic]
        """
        self.console.print(Panel(completion_msg, border_style="green", padding=(1, 2)))

    def _display_error(self, error: str):
        """Display an error message."""
        self.console.print(f"\n[bold red]Error:[/bold red] {error}\n")


def create_cli() -> CLI:
    """Factory function to create a CLI instance."""
    return CLI()
