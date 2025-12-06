# Guided Learning System

A multi-agent educational platform that provides adaptive, personalized learning experiences using AI agents.

## Architecture Overview

The system implements a sophisticated orchestration workflow with 4 specialized agents:

1. **Path Generator Agent** 🗺️ - Creates diverse, atomic learning paths from lesson objectives
2. **Evaluator Agent** ✅ - Assesses learner understanding and provides strategic guidance (deterministic, temp=0.1)
3. **Tutor Agent** 👨‍🏫 - Delivers engaging teaching content with active recall questions (creative, temp=0.5)
4. **Pedagogical Reviewer Agent** 🎓 - Ensures quality against 7 learning principles

### Core Workflow

```
Path Selection → Tutor Output → User Response → Evaluator Assessment
→ [Advance to next node] OR [Remediate same node] → Reviewer QC → Loop
```

### Key Features

- **Adaptive Remediation**: Automatically stays on concepts until mastery
- **Quality Control**: 3-retry reviewer loop with safety bypass
- **State Management**: Robust session state prevents hallucinations
- **7 Learning Principles**: Active learning, cognitive load management, ZPD scaffolding, and more
- **Field Agnostic**: Works for any subject matter

## Usage

### Basic Usage

Run a lesson from a lesson plan file:

```bash
python main.py path/to/LessonPlan_M2.json --lesson-number 1
```

### List Available Lessons

To see all lessons in a lesson plan:

```bash
python main.py path/to/LessonPlan_M2.json --list-lessons
```

### Command-Line Options

```
usage: main.py [-h] [--lesson-number LESSON_NUMBER] [--list-lessons]
               [--log-level {DEBUG,INFO,WARNING,ERROR}] [--log-file LOG_FILE]
               lesson_file

positional arguments:
  lesson_file           Path to the lesson plan JSON file

optional arguments:
  --lesson-number N     Which lesson to load from the plan (default: 1)
  --list-lessons        List all lessons in the file and exit
  --log-level LEVEL     Logging level (default: DEBUG)
  --log-file FILE       Log file path (default: guided_learning.log)
```

### Example Session

```bash
# Run lesson 1 from the Kubernetes module
python main.py ../LessonPlan_M2.json --lesson-number 1

# The system will:
# 1. Generate 2-3 diverse learning paths
# 2. Let you choose your preferred approach
# 3. Guide you through interactive learning
# 4. Adapt based on your responses
# 5. Ensure mastery before advancing
```

## Project Structure

```
guided_learning_system/
├── agents/                 # AI agent implementations
│   ├── path_generator.py  # Path Generator Agent
│   ├── evaluator.py       # Evaluator Agent
│   ├── tutor.py           # Tutor Agent
│   └── reviewer.py        # Pedagogical Reviewer Agent
├── core/                   # Core system components
│   ├── state.py           # Session state management
│   ├── orchestrator.py    # Orchestration engine
│   ├── llm_client.py      # Groq API wrapper
│   ├── lesson_loader.py   # Lesson plan loader
│   └── logging_config.py  # Logging configuration
├── cli/                    # Command-line interface
│   └── interface.py       # Rich-based CLI
├── config.py              # System configuration
├── main.py                # Entry point
├── requirements.txt       # Dependencies
└── README.md             # This file
```

## Configuration

### Model Configuration

Edit `config.py` to change models or temperatures:

```python
@dataclass
class ModelConfig:
    default_model: str = "llama-3.3-70b-versatile"  # Change model here

    # Agent-specific temperatures
    evaluator_temp: float = 0.1    # Deterministic
    tutor_temp: float = 0.5        # Creative
    # ...
```

### System Configuration

```python
@dataclass
class SystemConfig:
    max_reviewer_retries: int = 3      # Reviewer retry limit
    evaluator_history_window: int = 2  # Context for evaluator
    tutor_history_window: int = 6      # Context for tutor
    # ...
```

## Logging

The system provides comprehensive logging for debugging:

- **Console**: INFO level and above
- **File** (`guided_learning.log`): DEBUG level with full details

Log format:
```
2025-11-30 10:30:45 | INFO     | core.orchestrator | Processing user response
2025-11-30 10:30:46 | DEBUG    | agents.evaluator | Evaluation: intent=attempt_answer, advance=true
```

## Lesson Plan Format

Input lesson plans should follow this JSON structure:

```json
{
  "metadata": {
    "learning_goal": "Topic Name",
    "experience_level": "Beginner",
    "module_number": 1
  },
  "lesson_plan": {
    "module_title": "Module Title",
    "lessons": [
      {
        "lesson_number": 1,
        "title": "Lesson Title",
        "topics_covered": ["Topic 1", "Topic 2"],
        "learning_objectives": [
          "Objective 1",
          "Objective 2"
        ]
      }
    ]
  }
}
```

## Architecture Details

### State Machine Flow

1. **Initialization**: Path Generator creates diverse paths
2. **Path Selection**: User chooses learning approach
3. **Teaching Loop**:
   - Tutor generates content (first time: no evaluation)
   - User responds
   - Evaluator assesses understanding
   - Decision: Advance or Remediate
   - Tutor generates next output (with evaluator guidance)
   - Reviewer ensures quality (max 3 retries)
   - Repeat until lesson complete

### State Transition Rules

- **Advance**: `current_index++` ONLY when `evaluator.should_advance == true`
- **Remediate**: Stay on current node, tutor uses evaluator guidance
- **Complete**: When all nodes are finished with understanding verified

### The 7 Learning Principles

1. **Active Learning** - Generation effect, not just recognition
2. **Cognitive Load Management** - One concept per turn
3. **Adaptive Scaffolding (ZPD)** - Appropriate challenge level
4. **Misconception Diagnosis** - Errors as learning signals
5. **Curiosity & Relevance** - Concrete hooks and examples
6. **Emotional Awareness** - Supportive, encouraging tone
7. **Interleaving & Transfer** - Build transferable skills

## Troubleshooting

### API Key Issues

```
ValueError: GROQ_API_KEY environment variable not set
```

**Solution**: Set your API key:
```bash
export GROQ_API_KEY='your-key-here'
```

### Import Errors

**Solution**: Make sure you're running from the project directory:
```bash
cd guided_learning_system
python main.py ...
```

### Dependency Issues

**Solution**: Reinstall dependencies:
```bash
pip install --upgrade -r requirements.txt
```

## Development

### Adding New Agents

1. Create agent file in `agents/` directory
2. Implement agent logic with proper prompts
3. Register in `agents/__init__.py`
4. Integrate into `core/orchestrator.py`

### Customizing Prompts

All agent prompts are in their respective files:
- `agents/path_generator.py` - Path generation logic
- `agents/evaluator.py` - Evaluation criteria
- `agents/tutor.py` - Teaching approach
- `agents/reviewer.py` - Quality principles

## License

This project is part of the Nebula learning system.

## Credits

Built following the Unified Multi-Agent Guided Learning Architecture specification.
