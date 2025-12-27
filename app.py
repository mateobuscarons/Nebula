"""
FastAPI Backend for Adaptive Learning OS - Multi-tenant with Supabase Auth
Exposes REST API for personalized technical learning with AI agents
"""

import os
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv

from agents.learning_path import LearningPathAgent
from agents.module_planner import ModulePlannerAgent

from database.db_operations import Database
from mastery_engine.engine import MasteryEngine

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Adaptive Learning OS API",
    description="Backend API for personalized technical learning with AI agents - Multi-tenant",
    version="2.0.0"
)

# CORS configuration - allow frontend URL
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        frontend_url,
        "http://localhost:5173",  # Local development
        "http://localhost:3000",  # Alternative local port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client for auth verification
supabase_url = os.getenv("SUPABASE_URL")
supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_service_key:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables")

supabase: Client = create_client(supabase_url, supabase_service_key)

# Initialize PostgreSQL database
db = Database()

# In-memory storage for active lesson sessions (per user)
# Key: (user_id, module_num, challenge_num)
active_lessons: Dict[tuple, MasteryEngine] = {}


# ============================================================
# AUTHENTICATION DEPENDENCY
# ============================================================

async def get_current_user(authorization: str = Header(None)) -> str:
    """
    Verify JWT token and extract user_id from Supabase auth

    Args:
        authorization: Bearer token from request header

    Returns:
        user_id (UUID string) from verified token

    Raises:
        HTTPException: If token is missing or invalid
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization.replace("Bearer ", "")

    try:
        # Verify token with Supabase
        user_response = supabase.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        return user_response.user.id

    except Exception as e:
        print(f"❌ Auth error: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")


# ============================================================
# PYDANTIC MODELS
# ============================================================

class SetupRequest(BaseModel):
    """Initial setup request"""
    learning_goal: str  # What the user wants to achieve (objective)
    user_context: str = ""  # What the user already knows (baseline)


class PathApprovalRequest(BaseModel):
    """Learning path approval/editing request"""
    learning_path: Dict[str, Any]


class PathAdjustmentRequest(BaseModel):
    """Learning path adjustment request with user feedback"""
    learning_path: Dict[str, Any]
    user_feedback: str


class SessionResponse(BaseModel):
    """Session state response"""
    state: str
    user_profile: Optional[Dict[str, Any]] = None
    learning_path: Optional[Dict[str, Any]] = None
    current_challenge: Optional[Dict[str, Any]] = None
    progress_summary: Optional[Dict[str, Any]] = None


class LessonStartRequest(BaseModel):
    """Request to start a lesson"""
    module_number: int
    challenge_number: int


class LessonRespondRequest(BaseModel):
    """Request to respond to a lesson"""
    module_number: int
    challenge_number: int
    user_input: str


class LessonSource(BaseModel):
    """Single source reference"""
    title: str
    url: str
    domain: str
    description: Optional[str] = None  # Brief description of what this source covers


class LessonSources(BaseModel):
    """Sources grounding for a lesson"""
    sources: list[LessonSource] = []
    industry_insight: Optional[str] = None
    insight_source: Optional[str] = None  # URL backing the insight
    grounded: bool = False


class LessonResponse(BaseModel):
    """Response from lesson interaction"""
    conversation_content: str
    editor_content: Optional[Dict[str, Any]] = None
    lesson_status: Dict[str, Any]
    lesson_info: Optional[Dict[str, Any]] = None
    sources: Optional[LessonSources] = None


# ============================================================
# PUBLIC ENDPOINTS (No authentication required)
# ============================================================

@app.get("/")
def root():
    """Health check endpoint - public"""
    return {
        "status": "ok",
        "service": "Adaptive Learning OS API",
        "version": "2.0.0",
        "authentication": "Supabase Auth"
    }


# ============================================================
# PROTECTED ENDPOINTS (Authentication required)
# ============================================================

@app.get("/session", response_model=SessionResponse)
def get_session(user_id: str = Depends(get_current_user)):
    """
    Load or initialize user session

    Returns:
        - new_user: No user profile exists, need to run setup
        - path_approval: Learning path generated, awaiting approval
        - dashboard: Learning path approved, ready to view modules
    """
    # Update last active timestamp
    db.update_user_last_active(user_id)

    # Get or create user profile
    user_profile = db.get_user_profile(user_id)

    print(f"🔍 /session: User {user_id[:8]}... | Profile exists: {user_profile is not None}")

    if not user_profile:
        print(f"   → Returning state: new_user (no profile)")
        return SessionResponse(
            state="new_user",
            user_profile=None,
            learning_path=None,
            current_challenge=None,
            progress_summary=None
        )

    learning_path = db.get_learning_path(user_id)
    print(f"   Learning path found: {learning_path is not None}")

    if not learning_path:
        print(f"   → Returning state: new_user (profile exists but no learning path)")
        return SessionResponse(
            state="new_user",
            user_profile=user_profile,
            learning_path=None,
            current_challenge=None,
            progress_summary=None
        )

    module_challenges = db.get_all_module_challenges(user_id)

    if not module_challenges:
        return SessionResponse(
            state="path_approval",
            user_profile=user_profile,
            learning_path=learning_path,
            current_challenge=None,
            progress_summary=None
        )

    progress_summary = db.get_progress_summary(user_id)

    return SessionResponse(
        state="dashboard",
        user_profile=user_profile,
        learning_path=learning_path,
        current_challenge=None,
        progress_summary=progress_summary
    )


@app.post("/setup")
def setup(request: SetupRequest, user_id: str = Depends(get_current_user)):
    """
    Initial setup - Generate learning path

    Process:
        1. Create or update user profile
        2. Run Learning Path Agent
        3. Save learning path to database

    Returns:
        - user_id
        - learning_path (for approval/editing)
    """
    try:
        # Create or update user profile
        user_profile = db.create_or_get_user_profile(
            user_id=user_id,
            learning_goal=request.learning_goal,
            user_context=request.user_context
        )

        print(f"🚀 Generating learning path for user {user_id[:8]}...")
        print(f"   Goal: {request.learning_goal[:50]}...")

        agent = LearningPathAgent()

        # The agent takes user_context (baseline) and user_goal (objective)
        learning_path_result = agent.generate(
            user_context=request.user_context,
            user_goal=request.learning_goal
        )

        # The agent returns {"learning_path": {...}}
        learning_path_content = learning_path_result.get("learning_path", {})

        learning_path_data = {
            "input": {
                "user_baseline": request.user_context,
                "user_objective": request.learning_goal
            },
            "learning_path": learning_path_content
        }

        path_id = db.save_learning_path(user_id, learning_path_data)
        # Support both old (curriculum) and new (chapters) schema
        chapters = learning_path_content.get('chapters', learning_path_content.get('curriculum', []))
        num_chapters = len(chapters)
        print(f"✅ Learning path generated: {num_chapters} chapters")

        # Log token usage
        token_usage = learning_path_result.get("token_usage")
        if token_usage:
            db.log_token_usage(
                user_id=user_id,
                agent_name="learning_path",
                prompt_tokens=token_usage["prompt_tokens"],
                completion_tokens=token_usage["completion_tokens"],
                total_tokens=token_usage["total_tokens"],
                model_name=token_usage["model_name"]
            )
            print(f"📊 Token usage logged: {token_usage['total_tokens']} tokens")

        return {
            "success": True,
            "user_id": user_id,
            "learning_path": learning_path_data,
            "message": f"Generated {num_chapters} chapters"
        }

    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Setup failed: {str(e)}")


@app.post("/path/adjust")
def adjust_path(request: PathAdjustmentRequest, user_id: str = Depends(get_current_user)):
    """
    Adjust learning path based on user feedback

    This endpoint uses the regenerate_with_feedback method to iteratively
    improve the learning path until user approval.

    Returns:
        - user_id
        - learning_path (adjusted version)
    """
    try:
        # Extract the learning path data
        learning_path_data = request.learning_path
        original_path = learning_path_data["learning_path"]
        # Support both old and new field names
        learning_goal = learning_path_data["input"].get("user_objective") or learning_path_data["input"].get("learning_goal", "")
        user_baseline = learning_path_data["input"].get("user_baseline", "")

        print(f"🔄 Adjusting learning path for user {user_id[:8]}...")
        print(f"   Feedback: {request.user_feedback}")

        # Use the agent to regenerate with feedback
        agent = LearningPathAgent()
        adjusted_result = agent.regenerate_with_feedback(
            original_path=original_path,
            user_feedback=request.user_feedback,
            learning_goal=learning_goal
        )

        # The agent returns {"learning_path": {...}}
        adjusted_path_content = adjusted_result.get("learning_path", {})

        # Create new learning path data structure
        adjusted_learning_path_data = {
            "input": {
                "user_baseline": user_baseline,
                "user_objective": learning_goal
            },
            "learning_path": adjusted_path_content
        }

        # Update the learning path in database
        db.update_learning_path(user_id, adjusted_learning_path_data)

        # Support both old (curriculum) and new (chapters) schema
        chapters = adjusted_path_content.get('chapters', adjusted_path_content.get('curriculum', []))
        num_chapters = len(chapters)
        print(f"✅ Learning path adjusted: {num_chapters} chapters")

        # Log token usage
        token_usage = adjusted_result.get("token_usage")
        if token_usage:
            db.log_token_usage(
                user_id=user_id,
                agent_name="learning_path_adjust",
                prompt_tokens=token_usage["prompt_tokens"],
                completion_tokens=token_usage["completion_tokens"],
                total_tokens=token_usage["total_tokens"],
                model_name=token_usage["model_name"]
            )
            print(f"📊 Token usage logged: {token_usage['total_tokens']} tokens")

        return {
            "success": True,
            "user_id": user_id,
            "learning_path": adjusted_learning_path_data,
            "message": f"Adjusted to {num_chapters} chapters based on feedback"
        }

    except Exception as e:
        print(f"❌ Path adjustment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Path adjustment failed: {str(e)}")


@app.post("/path/approve")
def approve_path(request: PathApprovalRequest, user_id: str = Depends(get_current_user)):
    """
    Approve learning path and generate module challenges using URAC framework

    This is when we generate all module challenges using the Module Planner Agent
    with the URAC (Understand, Retain, Apply, Connect) framework.

    Returns:
        - success
        - total_modules
        - total_challenges
    """
    try:
        learning_path = request.learning_path["learning_path"]
        # Support both old and new field names
        user_objective = request.learning_path["input"].get("user_objective") or request.learning_path["input"].get("learning_goal", "")
        user_baseline = request.learning_path["input"].get("user_baseline", "")

        # Support both old (curriculum) and new (chapters) schema
        chapters = learning_path.get("chapters", learning_path.get("curriculum", []))

        print(f"\n🚀 Generating URAC lesson plans for user {user_id[:8]}... ({len(chapters)} chapters)")

        # Initialize the Module Planner Agent with gemini
        planner_agent = ModulePlannerAgent(model_provider="gemini")
        total_challenges = 0

        # Track acquired knowledge across modules
        acquired_knowledge_history = []

        for i, chapter in enumerate(chapters):
            # Support both old (module_order) and new (chapter) schema
            chapter_num = chapter.get("chapter", chapter.get("module_order", i + 1))
            print(f"\n   📘 Chapter {chapter_num}: {chapter['title']}")

            # Run the module planner agent with URAC framework
            lesson_plan_result = planner_agent.plan_module(
                user_baseline=user_baseline,
                user_objective=user_objective,
                current_module=chapter,
                acquired_knowledge_history=acquired_knowledge_history
            )

            # Count challenges (one per lesson in the URAC framework)
            num_challenges = len(lesson_plan_result.get("lesson_plan", []))

            # Build challenges list from URAC lesson plan
            challenges_list = []
            for lesson in lesson_plan_result.get("lesson_plan", []):
                urac = lesson.get("urac_blueprint", {})
                challenges_list.append({
                    "challenge_number": lesson["sequence"],
                    "topic": lesson["topic"],
                    "urac_blueprint": {
                        "understand": urac.get("understand", ""),
                        "retain": urac.get("retain", ""),
                        "apply": urac.get("apply", ""),
                        "connect": urac.get("connect", "")
                    }
                })

            # Save module challenges with URAC structure
            challenges_data = {
                "module": chapter,
                "module_id": lesson_plan_result.get("module_id", chapter_num),
                "module_context_bridge": lesson_plan_result.get("module_context_bridge", ""),
                "lesson_plan": lesson_plan_result.get("lesson_plan", []),
                "acquired_competencies": lesson_plan_result.get("acquired_competencies", []),
                "challenge_roadmap": {
                    "total_challenges": num_challenges,
                    "challenges": challenges_list
                }
            }

            db.save_module_challenges(user_id, chapter_num, challenges_data)
            db.initialize_module_progress(user_id, chapter_num, num_challenges)

            # Log token usage from module planner
            token_usage = lesson_plan_result.get("token_usage")
            if token_usage:
                db.log_token_usage(
                    user_id=user_id,
                    agent_name="module_planner",
                    prompt_tokens=token_usage["prompt_tokens"],
                    completion_tokens=token_usage["completion_tokens"],
                    total_tokens=token_usage["total_tokens"],
                    model_name=token_usage["model_name"]
                )

            # Update acquired knowledge history for next chapter
            acquired_knowledge_history.extend(
                lesson_plan_result.get("acquired_competencies", [])
            )

            total_challenges += num_challenges
            print(f"      ✅ {num_challenges} URAC challenges created")

        print(f"\n✨ Total: {total_challenges} challenges across {len(chapters)} chapters")

        return {
            "success": True,
            "total_chapters": len(chapters),
            "total_challenges": total_challenges,
            "message": f"Learning path finalized with {total_challenges} URAC-based challenges"
        }

    except Exception as e:
        print(f"❌ Path approval failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Path approval failed: {str(e)}")


@app.get("/progress")
def get_progress(user_id: str = Depends(get_current_user)):
    """
    Get overall progress summary with individual challenge completion status

    Returns:
        - modules (list with progress per module and individual challenge status)
        - total_completed
        - total_challenges
        - current_module
        - current_challenge
    """
    try:
        return db.get_progress_summary(user_id)

    except Exception as e:
        print(f"❌ Failed to get progress: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get progress: {str(e)}")


@app.get("/challenges/metadata")
def get_all_challenges_metadata(user_id: str = Depends(get_current_user)):
    """
    Get all challenge titles and URAC metadata for dashboard display

    Returns:
        Dictionary mapping module_number to module and challenge metadata with URAC framework
    """
    try:
        all_module_challenges = db.get_all_module_challenges(user_id)

        metadata = {}
        for module_data in all_module_challenges:
            module_num = module_data["module_number"]
            module_info = module_data.get("module", {})
            challenges = module_data["challenge_roadmap"]["challenges"]

            # Get module metadata from the new structure
            module_context_bridge = module_data.get("module_context_bridge", "")
            acquired_competencies = module_data.get("acquired_competencies", [])

            metadata[module_num] = {
                "module_title": module_info.get("title", f"Module {module_num}"),
                "module_description": module_info.get("competency_goal", ""),
                "module_context_bridge": module_context_bridge,
                "acquired_competencies": acquired_competencies,
                "challenges": [
                    {
                        "challenge_number": c["challenge_number"],
                        "topic": c.get("topic", ""),
                        "urac_blueprint": c.get("urac_blueprint", {
                            "understand": "",
                            "retain": "",
                            "apply": "",
                            "connect": ""
                        })
                    }
                    for c in challenges
                ]
            }

        return metadata

    except Exception as e:
        print(f"❌ Failed to get challenges metadata: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get challenges metadata: {str(e)}")


@app.post("/lesson/start", response_model=LessonResponse)
def start_lesson(request: LessonStartRequest, user_id: str = Depends(get_current_user)):
    """
    Start an interactive lesson using the Mastery Engine.

    Process:
        1. Validate user and sequential access
        2. Load lesson data from module_challenges
        3. Initialize MasteryEngine with lesson data
        4. Mark challenge as in_progress
        5. Get initial AI response

    Returns:
        LessonResponse with conversation_content, editor_content, lesson_status
    """
    try:
        # Update last active timestamp
        db.update_user_last_active(user_id)

        module_num = request.module_number
        challenge_num = request.challenge_number

        print(f"\n🎓 Starting lesson for user {user_id[:8]}: Module {module_num}, Challenge {challenge_num}")

        # Validate sequential access
        if challenge_num > 1:
            prev_progress = db.get_challenge_progress(user_id, module_num, challenge_num - 1)
            if not prev_progress or prev_progress["status"] != "completed":
                raise HTTPException(
                    status_code=403,
                    detail=f"Must complete challenge {challenge_num - 1} first"
                )

        # Check if challenge is already completed
        current_progress = db.get_challenge_progress(user_id, module_num, challenge_num)
        if current_progress and current_progress["status"] == "completed":
            raise HTTPException(
                status_code=403,
                detail="This lesson has already been completed"
            )

        # Load module challenges from DB
        module_challenges = db.get_module_challenges(user_id, module_num)
        if not module_challenges:
            raise HTTPException(
                status_code=404,
                detail=f"Module {module_num} challenges not found"
            )

        # Get the specific lesson from the lesson_plan
        lesson_plan = module_challenges.get("lesson_plan", [])
        lesson_data = None
        for lesson in lesson_plan:
            if lesson.get("sequence") == challenge_num:
                lesson_data = lesson
                break

        if not lesson_data:
            raise HTTPException(
                status_code=404,
                detail=f"Challenge {challenge_num} not found in module {module_num}"
            )

        # Get user context from learning path
        learning_path = db.get_learning_path(user_id)
        user_baseline = learning_path.get("input", {}).get("user_baseline", "") if learning_path else ""
        user_objective = learning_path.get("input", {}).get("user_objective", "") if learning_path else ""

        # Build acquired knowledge from previous modules/challenges
        acquired_knowledge = []

        print(f"\n📚 Building Acquired Knowledge...")
        print(f"   Current: Module {module_num}, Challenge {challenge_num}")

        # Add knowledge from previous modules
        all_module_challenges = db.get_all_module_challenges(user_id)
        print(f"   Total modules in DB: {len(all_module_challenges)}")

        for mc in all_module_challenges:
            mc_num = mc["module_number"]
            mc_competencies = mc.get("acquired_competencies", [])
            print(f"   Module {mc_num}: {len(mc_competencies)} competencies available")

            if mc_num < module_num:
                # Add all competencies from previous modules
                acquired_knowledge.extend(mc_competencies)
                print(f"      ✅ Added all {len(mc_competencies)} competencies (previous module)")
            elif mc_num == module_num:
                # Add knowledge from previous challenges in current module
                competencies_to_add = min(challenge_num - 1, len(mc_competencies))
                if competencies_to_add > 0:
                    for i in range(competencies_to_add):
                        acquired_knowledge.append(mc_competencies[i])
                    print(f"      ✅ Added {competencies_to_add} competencies (previous challenges in current module)")
                else:
                    print(f"      ⏭️  No previous challenges to add (first challenge)")

        print(f"\n   📋 Total Acquired Knowledge: {len(acquired_knowledge)} items")
        if acquired_knowledge:
            print(f"   📝 Acquired knowledge preview:")
            for i, knowledge in enumerate(acquired_knowledge[:3], 1):
                preview = knowledge[:80] + "..." if len(knowledge) > 80 else knowledge
                print(f"      {i}. {preview}")
            if len(acquired_knowledge) > 3:
                print(f"      ... and {len(acquired_knowledge) - 3} more")
        else:
            print(f"   ℹ️  No acquired knowledge (first lesson)")

        # Initialize MasteryEngine
        engine = MasteryEngine()
        engine.load_lesson_from_data(
            user_baseline=user_baseline,
            user_objective=user_objective,
            module_data=module_challenges,
            lesson_index=challenge_num - 1,  # 0-indexed
            acquired_knowledge=acquired_knowledge
        )

        # Store in active lessons
        session_key = (user_id, module_num, challenge_num)
        active_lessons[session_key] = engine

        # Mark challenge as in_progress
        db.update_challenge_status(user_id, module_num, challenge_num, "in_progress")

        # Step 1: Ground the lesson (fetch sources BEFORE teaching)
        grounding_result = engine.ground_lesson()

        # Log grounding token usage
        db.log_token_usage(
            user_id=user_id,
            agent_name="lesson_grounding",
            prompt_tokens=100,  # Approximate for grounding call
            completion_tokens=200,
            total_tokens=300,
            model_name="gemini-2.5-flash"
        )

        # Step 2: Start the lesson (teaching content informed by grounding)
        response = engine.start_lesson()

        # Log teaching token usage
        if engine.last_token_usage:
            db.log_token_usage(
                user_id=user_id,
                agent_name="mastery_engine",
                prompt_tokens=engine.last_token_usage.get("input_tokens", 0),
                completion_tokens=engine.last_token_usage.get("output_tokens", 0),
                total_tokens=engine.last_token_usage.get("total_tokens", 0),
                model_name=engine.model_name
            )

        print(f"   ✅ Lesson started, phase: {response.get('lesson_status', {}).get('current_phase', 'UNKNOWN')}")

        # Build sources response
        sources_data = None
        if grounding_result.get("grounded"):
            sources_data = LessonSources(
                sources=[LessonSource(**s) for s in grounding_result.get("sources", [])],
                industry_insight=grounding_result.get("industry_insight"),
                insight_source=grounding_result.get("insight_source"),
                grounded=True
            )

        return LessonResponse(
            conversation_content=response.get("conversation_content", ""),
            editor_content=response.get("editor_content"),
            lesson_status=response.get("lesson_status", {}),
            lesson_info={
                "module_number": module_num,
                "challenge_number": challenge_num,
                "topic": lesson_data.get("topic", ""),
                "module_title": module_challenges.get("module", {}).get("title", f"Module {module_num}")
            },
            sources=sources_data
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Failed to start lesson: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start lesson: {str(e)}")


@app.post("/lesson/respond", response_model=LessonResponse)
def respond_to_lesson(request: LessonRespondRequest, user_id: str = Depends(get_current_user)):
    """
    Process user response in an active lesson.

    Process:
        1. Get active MasteryEngine instance
        2. Process user input
        3. If completed, mark challenge as completed
        4. Return AI response

    Returns:
        LessonResponse with conversation_content, editor_content, lesson_status
    """
    try:
        # Update last active timestamp
        db.update_user_last_active(user_id)

        module_num = request.module_number
        challenge_num = request.challenge_number
        user_input = request.user_input

        print(f"\n📝 Processing response for user {user_id[:8]}: Module {module_num}, Challenge {challenge_num}")
        print(f"   User input: {user_input[:100]}..." if len(user_input) > 100 else f"   User input: {user_input}")

        # Get active lesson engine
        session_key = (user_id, module_num, challenge_num)
        engine = active_lessons.get(session_key)

        if not engine:
            raise HTTPException(
                status_code=404,
                detail="No active lesson found. Please start the lesson first."
            )

        # Process user input
        response = engine.process_user_input(user_input)

        # Log token usage from mastery engine
        if engine.last_token_usage:
            db.log_token_usage(
                user_id=user_id,
                agent_name="mastery_engine",
                prompt_tokens=engine.last_token_usage.get("input_tokens", 0),
                completion_tokens=engine.last_token_usage.get("output_tokens", 0),
                total_tokens=engine.last_token_usage.get("total_tokens", 0),
                model_name=engine.model_name
            )

        # Check if lesson is completed
        lesson_status = response.get("lesson_status", {})
        current_phase = lesson_status.get("current_phase", "")

        if current_phase == "COMPLETED":
            print(f"   🎉 Lesson completed!")
            db.complete_challenge(user_id, module_num, challenge_num)
            # Clean up active lesson
            del active_lessons[session_key]

        print(f"   ✅ Response processed, phase: {current_phase}")

        # Get lesson info for response
        module_challenges = db.get_module_challenges(user_id, module_num)
        lesson_plan = module_challenges.get("lesson_plan", []) if module_challenges else []
        lesson_data = None
        for lesson in lesson_plan:
            if lesson.get("sequence") == challenge_num:
                lesson_data = lesson
                break

        return LessonResponse(
            conversation_content=response.get("conversation_content", ""),
            editor_content=response.get("editor_content"),
            lesson_status=lesson_status,
            lesson_info={
                "module_number": module_num,
                "challenge_number": challenge_num,
                "topic": lesson_data.get("topic", "") if lesson_data else "",
                "module_title": module_challenges.get("module", {}).get("title", f"Module {module_num}") if module_challenges else f"Module {module_num}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Failed to process response: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process response: {str(e)}")


# ============================================================
# USER DATA MANAGEMENT
# ============================================================

@app.post("/reset")
def reset_user_data(user_id: str = Depends(get_current_user)):
    """
    Reset user's learning path data to start fresh.
    Deletes learning path, module challenges, and progress.
    Keeps user profile.

    Returns:
        - success: True if reset completed
    """
    try:
        print(f"🔄 Resetting data for user {user_id[:8]}...")

        # Delete in correct order due to dependencies
        db.delete_user_progress(user_id)
        db.delete_user_module_challenges(user_id)
        db.delete_user_learning_path(user_id)

        # Clean up any active lessons for this user
        keys_to_delete = [key for key in active_lessons.keys() if key[0] == user_id]
        for key in keys_to_delete:
            del active_lessons[key]

        print(f"✅ User data reset successfully")

        return {
            "success": True,
            "message": "Learning path and progress reset. You can now create a new learning path."
        }

    except Exception as e:
        print(f"❌ Reset failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


# ============================================================
# ADMIN ENDPOINTS
# ============================================================

@app.get("/admin/stats")
def get_admin_stats(user_id: str = Depends(get_current_user)):
    """
    Get admin statistics (token usage, user activity)

    Returns:
        Admin dashboard data with token usage and user stats
    """
    try:
        # Check if user is admin
        if not db.is_admin(user_id):
            raise HTTPException(status_code=403, detail="Admin access required")

        # Get statistics
        stats = db.get_admin_statistics()
        return stats

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Failed to get admin stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get admin stats: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
