"""
FastAPI Backend for Adaptive Learning OS
Exposes REST API for learning path and module planning workflow
"""

import os
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.learning_path import LearningPathAgent
from agents.module_planner import ModulePlannerAgent

from database.db_operations import Database

app = FastAPI(
    title="Adaptive Learning OS API",
    description="Backend API for personalized technical learning with AI agents",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database(db_path="learning_system.db")


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

@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Adaptive Learning OS API",
        "version": "1.0.0"
    }


@app.get("/session", response_model=SessionResponse)
def get_session():
    """
    Load or initialize user session

    Returns:
        - new_user: No user exists, need to run setup
        - path_approval: Learning path generated, awaiting approval
        - dashboard: Learning path approved, ready to view modules
    """
    user = db.get_first_user_profile()
    print(f"🔍 /session: User found: {user is not None} (ID: {user['id'] if user else 'N/A'})")

    if not user:
        print(f"   → Returning state: new_user (no user)")
        return SessionResponse(
            state="new_user",
            user_profile=None,
            learning_path=None,
            current_challenge=None,
            progress_summary=None
        )

    learning_path = db.get_learning_path(user["id"])
    print(f"   Learning path found: {learning_path is not None}")

    if not learning_path:
        print(f"   → Returning state: new_user (user exists but no learning path)")
        return SessionResponse(
            state="new_user",
            user_profile=user,
            learning_path=None,
            current_challenge=None,
            progress_summary=None
        )

    module_challenges = db.get_all_module_challenges(user["id"])

    if not module_challenges:
        return SessionResponse(
            state="path_approval",
            user_profile=user,
            learning_path=learning_path,
            current_challenge=None,
            progress_summary=None
        )

    progress_summary = db.get_progress_summary(user["id"])

    return SessionResponse(
        state="dashboard",
        user_profile=user,
        learning_path=learning_path,
        current_challenge=None,
        progress_summary=progress_summary
    )


@app.post("/setup")
def setup(request: SetupRequest):
    """
    Initial setup - Generate learning path

    Process:
        1. Get or create user profile (single-user MVP)
        2. Run Learning Path Agent
        3. Save learning path to database

    Returns:
        - user_id
        - learning_path (for approval/editing)
    """
    try:
        existing_user = db.get_first_user_profile()
        if existing_user:
            user_id = existing_user["id"]
            print(f"🔄 Using existing user: {user_id}")
        else:
            user_id = db.create_user_profile(
                learning_goal=request.learning_goal,
                user_context=request.user_context
            )

        print(f"🚀 Generating learning path for: {request.learning_goal}")
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
        num_modules = len(learning_path_content.get('curriculum', []))
        print(f"✅ Learning path generated: {num_modules} modules")

        return {
            "success": True,
            "user_id": user_id,
            "learning_path": learning_path_data,
            "message": f"Generated {num_modules} modules"
        }

    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Setup failed: {str(e)}")


@app.post("/path/adjust")
def adjust_path(request: PathAdjustmentRequest):
    """
    Adjust learning path based on user feedback
    
    This endpoint uses the regenerate_with_feedback method to iteratively
    improve the learning path until user approval.
    
    Returns:
        - user_id
        - learning_path (adjusted version)
    """
    try:
        user = db.get_first_user_profile()
        if not user:
            raise HTTPException(status_code=404, detail="No user profile found")
        
        user_id = user["id"]
        
        # Extract the learning path data
        learning_path_data = request.learning_path
        original_path = learning_path_data["learning_path"]
        # Support both old and new field names
        learning_goal = learning_path_data["input"].get("user_objective") or learning_path_data["input"].get("learning_goal", "")
        user_baseline = learning_path_data["input"].get("user_baseline", "")
        
        print(f"🔄 Adjusting learning path based on user feedback")
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
        
        num_modules = len(adjusted_path_content.get('curriculum', []))
        print(f"✅ Learning path adjusted: {num_modules} modules")
        
        return {
            "success": True,
            "user_id": user_id,
            "learning_path": adjusted_learning_path_data,
            "message": f"Adjusted to {num_modules} modules based on feedback"
        }
        
    except Exception as e:
        print(f"❌ Path adjustment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Path adjustment failed: {str(e)}")


@app.post("/path/approve")
def approve_path(request: PathApprovalRequest):
    """
    Approve learning path and generate module challenges using URAC framework

    This is when we generate all module challenges using the new Module Planner Agent
    with the URAC (Understand, Retain, Apply, Connect) framework.

    Returns:
        - success
        - total_modules
        - total_challenges
    """
    try:
        user = db.get_first_user_profile()
        if not user:
            raise HTTPException(status_code=404, detail="No user profile found")

        user_id = user["id"]

        learning_path = request.learning_path["learning_path"]
        # Support both old and new field names
        user_objective = request.learning_path["input"].get("user_objective") or request.learning_path["input"].get("learning_goal", "")
        user_baseline = request.learning_path["input"].get("user_baseline", "")

        # Use 'curriculum' key from the new format
        modules = learning_path.get("curriculum", [])

        print(f"\n🚀 Generating URAC lesson plans for {len(modules)} modules...")

        # Initialize the new Module Planner Agent with gemini
        planner_agent = ModulePlannerAgent(model_provider="gemini")
        total_challenges = 0

        # Track acquired knowledge across modules
        acquired_knowledge_history = []

        for i, module in enumerate(modules):
            # Use module_order from the new format
            module_num = module.get("module_order", i + 1)
            print(f"\n   📘 Module {module_num}: {module['title']}")

            # Run the module planner agent with URAC framework
            lesson_plan_result = planner_agent.plan_module(
                user_baseline=user_baseline,
                user_objective=user_objective,
                current_module=module,
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
                "module": module,
                "module_id": lesson_plan_result.get("module_id", module_num),
                "module_context_bridge": lesson_plan_result.get("module_context_bridge", ""),
                "lesson_plan": lesson_plan_result.get("lesson_plan", []),
                "acquired_competencies": lesson_plan_result.get("acquired_competencies", []),
                "challenge_roadmap": {
                    "total_challenges": num_challenges,
                    "challenges": challenges_list
                }
            }

            db.save_module_challenges(user_id, module_num, challenges_data)
            db.initialize_module_progress(user_id, module_num, num_challenges)

            # Update acquired knowledge history for next module
            acquired_knowledge_history.extend(
                lesson_plan_result.get("acquired_competencies", [])
            )

            total_challenges += num_challenges
            print(f"      ✅ {num_challenges} URAC challenges created")

        print(f"\n✨ Total: {total_challenges} challenges across {len(modules)} modules")

        return {
            "success": True,
            "total_modules": len(modules),
            "total_challenges": total_challenges,
            "message": f"Learning path finalized with {total_challenges} URAC-based challenges"
        }

    except Exception as e:
        print(f"❌ Path approval failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Path approval failed: {str(e)}")


@app.get("/progress")
def get_progress():
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
        user = db.get_first_user_profile()
        if not user:
            raise HTTPException(status_code=404, detail="No user profile found")

        user_id = user["id"]
        return db.get_progress_summary(user_id)

    except Exception as e:
        print(f"❌ Failed to get progress: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get progress: {str(e)}")


@app.get("/challenges/metadata")
def get_all_challenges_metadata():
    """
    Get all challenge titles and URAC metadata for dashboard display

    Returns:
        Dictionary mapping module_number to module and challenge metadata with URAC framework
    """
    try:
        user = db.get_first_user_profile()
        if not user:
            raise HTTPException(status_code=404, detail="No user profile found")

        user_id = user["id"]
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


@app.delete("/reset")
def reset_system():
    """
    Reset the entire system (for testing/development)
    Deletes all user data and learning paths
    """
    try:
        import os
        db_path = "learning_system.db"
        
        if os.path.exists(db_path):
            os.remove(db_path)
            print("🗑️  Deleted learning_system.db")
        
        # Reinitialize database
        global db
        db = Database(db_path=db_path)
        
        print("✅ System reset complete")
        return {"success": True, "message": "System reset successfully"}
    
    except Exception as e:
        print(f"❌ Reset failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
