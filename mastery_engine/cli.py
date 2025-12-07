"""
Mastery Engine CLI - Interactive Testing Interface

Provides a command-line interface to test the Mastery Engine.
Displays formatted output with System Debug, Chat, and Editor sections.
"""

import os
import sys
from typing import Dict, Any

# Handle both direct script execution and module execution
try:
    from .engine import MasteryEngine
except ImportError:
    from engine import MasteryEngine


class MasteryCLI:
    """
    Interactive CLI for testing the Mastery Engine.

    Displays:
    - Header with lesson progress
    - System Debug (acquired knowledge, tokens, latency)
    - Chat Bot (conversation content)
    - Editor State (code/text in a box)
    """

    def __init__(self, module_plans_file: str):
        """
        Initialize CLI with module plans file.

        Args:
            module_plans_file: Path to module_plans.json
        """
        self.engine = MasteryEngine()
        self.module_plans_file = module_plans_file
        self.editor_state = None  # Track current editor content

    def run(self):
        """Main CLI loop."""
        # Load lesson plans
        print(f"\n{'='*80}")
        print(f"MASTERY ENGINE - Interactive Learning System")
        print(f"{'='*80}\n")

        try:
            self.engine.load_lesson_plans(self.module_plans_file)
        except FileNotFoundError:
            print(f"❌ Error: Could not find {self.module_plans_file}")
            print(f"Please ensure the file exists in the current directory.")
            return
        except Exception as e:
            print(f"❌ Error loading lesson plans: {e}")
            return

        # Start lesson loop
        while True:
            lesson = self.engine.get_current_lesson()
            if not lesson:
                self._display_completion()
                break

            # Start the lesson (get initial LLM response)
            try:
                response = self.engine.start_lesson()
                self._display_response(response)
            except Exception as e:
                print(f"\n❌ Error starting lesson: {e}")
                break

            # Interaction loop for current lesson
            lesson_complete = False
            while not lesson_complete:
                # Get user input
                user_input = self._get_user_input()

                if user_input.lower() in ['/quit', '/exit', '/q']:
                    print("\n👋 Exiting Mastery Engine. Progress is not saved.")
                    return

                # Process user input
                try:
                    response = self.engine.process_user_input(user_input)

                    # Validate response is a dict
                    if not isinstance(response, dict):
                        print(f"\n❌ Internal Error: Expected dict response, got {type(response).__name__}")
                        print("The system may have returned malformed output. Please try again.\n")
                        continue

                    self._display_response(response)

                    # Check if lesson is completed
                    status = response.get("lesson_status", {})
                    if status.get("current_phase") == "COMPLETED":
                        lesson_complete = True

                except Exception as e:
                    print(f"\n❌ Error processing input: {e}")
                    print("Please try again.\n")

            # Advance to next lesson
            has_more = self.engine.advance_to_next_lesson()
            if has_more:
                print(f"\n{'─'*80}")
                print(f"✅ Lesson completed! Moving to next lesson...")
                print(f"{'─'*80}\n")
                input("Press Enter to continue...")
            else:
                # No more lessons
                break

    def _display_response(self, response: Dict[str, Any]):
        """
        Display formatted LLM response.

        Args:
            response: Structured JSON response from engine
        """
        # Display header
        self._display_header()

        # Display system debug info
        self._display_debug()

        # Display chat content
        self._display_chat(response.get("conversation_content", ""))

        # Display editor content (if any)
        editor_content = response.get("editor_content", {})
        if editor_content and editor_content.get("content"):
            self.editor_state = editor_content
            self._display_editor(editor_content)

    def _display_header(self):
        """Display lesson progress header."""
        progress = self.engine.get_progress_info()

        print(f"\n{'='*80}")
        print(f"MODULE {progress['current_module']}/{progress['total_modules']}: {progress['module_title']}")
        print(f"LESSON {progress['current_lesson']} - {progress['lesson_topic']}")
        print(f"{'='*80}\n")

    def _display_debug(self):
        """Display system debug information."""
        print(f"[System Debug]")
        print(f"📚 Acquired Knowledge:")

        acquired_knowledge = self.engine.get_acquired_knowledge()
        if acquired_knowledge:
            for knowledge in acquired_knowledge:
                print(f"   • {knowledge}")
        else:
            print(f"   (None - this is the first lesson)")

        # Display token usage and latency
        usage = self.engine.last_token_usage
        if usage:
            print(f"⏱️  Response Time: {self.engine.last_response_time:.1f}s")
            print(f"🔢 Tokens: {usage.get('total_tokens', 0):,} "
                  f"(In: {usage.get('input_tokens', 0):,}, Out: {usage.get('output_tokens', 0):,})")

        print()  # Blank line after debug section

    def _display_chat(self, content: str):
        """
        Display chat bot content.

        Args:
            content: The conversation_content from LLM
        """
        print(f"[Chat Bot]")
        print(content)
        print()  # Blank line after chat

    def _display_editor(self, editor_content: Dict[str, Any]):
        """
        Display editor content in a box.

        Args:
            editor_content: Editor content dict with type, language, content
        """
        content = editor_content.get("content", "")
        language = editor_content.get("language", "text")

        if not content:
            return

        print(f"[Editor State] ({language})")

        # Split content into lines
        lines = content.split('\n')

        # Calculate box width (max line length or 78, whichever is smaller)
        max_width = min(max(len(line) for line in lines) if lines else 0, 76)
        box_width = max(max_width, 40)  # Minimum width of 40

        # Top border
        print(f"┌{'─' * (box_width + 2)}┐")

        # Content lines
        for line in lines:
            # Pad line to box width
            padded_line = line.ljust(box_width)
            print(f"│ {padded_line} │")

        # Bottom border
        print(f"└{'─' * (box_width + 2)}┘")
        print()  # Blank line after editor

    def _get_user_input(self) -> str:
        """
        Get user input from command line.

        Returns:
            User input string
        """
        print(f"{'─'*80}")
        try:
            user_input = input("> Your response: ").strip()
            return user_input
        except EOFError:
            # Handle Ctrl+D
            print("\n\n👋 Exiting Mastery Engine.")
            sys.exit(0)
        except KeyboardInterrupt:
            # Handle Ctrl+C
            print("\n\n👋 Exiting Mastery Engine.")
            sys.exit(0)

    def _display_completion(self):
        """Display completion message when all lessons are done."""
        print(f"\n{'='*80}")
        print(f"🎉 CONGRATULATIONS! YOU'VE COMPLETED ALL LESSONS!")
        print(f"{'='*80}\n")

        print(f"📚 Total Knowledge Acquired:")
        acquired_knowledge = self.engine.get_acquired_knowledge()
        for knowledge in acquired_knowledge:
            print(f"   ✓ {knowledge}")

        print(f"\n{'='*80}")
        print(f"You've successfully completed the learning path!")
        print(f"{'='*80}\n")


def main():
    """Main entry point for CLI."""
    import sys

    # Check for .env file
    if not os.path.exists(".env"):
        print("\n⚠️  No .env file found!")
        print("Create .env with:")
        print("  GEMINI_API_KEY=your_key")
        sys.exit(1)

    # Default to module_plans.json in current directory
    module_plans_file = "module_plans.json"

    # Allow override via command line argument
    if len(sys.argv) > 1:
        module_plans_file = sys.argv[1]

    if not os.path.exists(module_plans_file):
        print(f"\n❌ Error: {module_plans_file} not found!")
        print(f"\nUsage: python -m mastery_engine.cli [module_plans_file]")
        print(f"Default: python -m mastery_engine.cli  (uses module_plans.json)")
        sys.exit(1)

    # Run CLI
    cli = MasteryCLI(module_plans_file)
    cli.run()


if __name__ == "__main__":
    main()
