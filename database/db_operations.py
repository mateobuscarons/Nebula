"""
Database operations for Adaptive Learning OS - PostgreSQL Multi-tenant Version
Handles all CRUD operations for user profiles, learning paths, module challenges, and progress tracking
"""

import os
import json
import threading
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from psycopg2 import pool
except ImportError:
    raise ImportError(
        "psycopg2 is required for PostgreSQL support. "
        "Install it with: pip install psycopg2-binary"
    )


class Database:
    """PostgreSQL database manager for multi-tenant learning system"""

    def __init__(self, db_url: str = None):
        """
        Initialize database connection pool

        Args:
            db_url: PostgreSQL connection string (defaults to DATABASE_URL env var)
        """
        self.db_url = db_url or os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError(
                "DATABASE_URL environment variable not set. "
                "Set it to your Supabase PostgreSQL connection string."
            )

        self._pool_lock = threading.Lock()
        self._create_pool()

    def _create_pool(self):
        """Create or recreate the connection pool"""
        try:
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                1,  # min connections
                10,  # max connections
                self.db_url,
                # Add keepalive settings to detect dead connections faster
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5
            )
        except Exception as e:
            print(f"❌ Failed to connect to PostgreSQL database: {e}")
            raise

    def _test_connection(self, conn) -> bool:
        """Test if a connection is still alive"""
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            return True
        except Exception:
            return False

    def _get_valid_connection(self):
        """Get a valid connection from the pool, handling stale connections"""
        max_retries = 3

        for attempt in range(max_retries):
            conn = None
            try:
                with self._pool_lock:
                    conn = self.connection_pool.getconn()

                # Test if connection is still alive
                if self._test_connection(conn):
                    return conn

                # Connection is dead, close it and try again
                with self._pool_lock:
                    try:
                        self.connection_pool.putconn(conn, close=True)
                    except Exception:
                        pass
                conn = None

                # On last attempt before giving up, recreate the pool
                if attempt == max_retries - 2:
                    print("🔄 Recreating connection pool due to stale connections...")
                    with self._pool_lock:
                        try:
                            self.connection_pool.closeall()
                        except Exception:
                            pass
                        self._create_pool()

            except Exception as e:
                if conn:
                    with self._pool_lock:
                        try:
                            self.connection_pool.putconn(conn, close=True)
                        except Exception:
                            pass
                if attempt < max_retries - 1:
                    print(f"⚠️ Failed to get connection (attempt {attempt + 1}/{max_retries}): {e}")
                    continue
                raise

        raise psycopg2.OperationalError("Failed to get a valid database connection after retries")

    @contextmanager
    def _get_connection(self):
        """Get database connection from pool with automatic cleanup"""
        conn = self._get_valid_connection()
        try:
            yield conn
        finally:
            with self._pool_lock:
                try:
                    self.connection_pool.putconn(conn)
                except Exception:
                    pass

    def _execute_query(self, query: str, params: tuple = None, fetch_one=False, fetch_all=False):
        """
        Execute a query with automatic connection management and retry logic

        Args:
            query: SQL query string
            params: Query parameters
            fetch_one: Return single row
            fetch_all: Return all rows

        Returns:
            Query result or None
        """
        max_retries = 3
        last_error = None

        # Check if this is a write operation (needs commit)
        query_upper = query.strip().upper()
        is_write_operation = query_upper.startswith(('INSERT', 'UPDATE', 'DELETE'))

        for attempt in range(max_retries):
            try:
                with self._get_connection() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        cur.execute(query, params or ())

                        if fetch_one:
                            result = cur.fetchone()
                            # Commit if this was a write operation (INSERT/UPDATE/DELETE with RETURNING)
                            if is_write_operation:
                                conn.commit()
                            return dict(result) if result else None
                        elif fetch_all:
                            results = cur.fetchall()
                            # Commit if this was a write operation
                            if is_write_operation:
                                conn.commit()
                            return [dict(row) for row in results]
                        else:
                            conn.commit()
                            return cur.rowcount
            except psycopg2.OperationalError as e:
                last_error = e
                if attempt < max_retries - 1:
                    print(f"⚠️ Query execution error (attempt {attempt + 1}/{max_retries}): {e}")
                    # Pool recreation is handled in _get_connection
                    continue
                raise
            except psycopg2.InterfaceError as e:
                # Connection was closed
                last_error = e
                if attempt < max_retries - 1:
                    print(f"⚠️ Connection closed (attempt {attempt + 1}/{max_retries}): {e}")
                    continue
                raise

        # Should not reach here, but just in case
        if last_error:
            raise last_error

    # ============================================================
    # USER PROFILE OPERATIONS
    # ============================================================

    def create_or_get_user_profile(
        self,
        user_id: str,
        learning_goal: str = None,
        user_context: str = None
    ) -> Dict[str, Any]:
        """
        Create or get user profile (learning preferences)

        Args:
            user_id: User UUID from Supabase auth
            learning_goal: What the user wants to achieve (objective)
            user_context: What the user already knows (baseline)

        Returns:
            User profile dict
        """
        # Try to get existing profile
        existing = self.get_user_profile(user_id)
        if existing:
            return existing

        # Create new profile
        if not learning_goal:
            learning_goal = ""
        if not user_context:
            user_context = ""

        query = """
            INSERT INTO user_profiles (user_id, learning_goal, user_context)
            VALUES (%s, %s, %s)
            RETURNING id, user_id, learning_goal, user_context, created_at, last_active
        """
        return self._execute_query(query, (user_id, learning_goal, user_context), fetch_one=True)

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile by user_id

        Args:
            user_id: User UUID

        Returns:
            User profile dict or None if not found
        """
        query = "SELECT * FROM user_profiles WHERE user_id = %s"
        return self._execute_query(query, (user_id,), fetch_one=True)

    def update_user_profile(self, user_id: str, learning_goal: str = None, user_context: str = None):
        """
        Update user profile

        Args:
            user_id: User UUID
            learning_goal: Updated learning goal
            user_context: Updated user context
        """
        updates = []
        params = []

        if learning_goal is not None:
            updates.append("learning_goal = %s")
            params.append(learning_goal)
        if user_context is not None:
            updates.append("user_context = %s")
            params.append(user_context)

        if not updates:
            return

        updates.append("last_active = NOW()")
        params.append(user_id)

        query = f"UPDATE user_profiles SET {', '.join(updates)} WHERE user_id = %s"
        self._execute_query(query, tuple(params))

    def update_user_last_active(self, user_id: str):
        """Update user's last_active timestamp"""
        query = "UPDATE user_profiles SET last_active = NOW() WHERE user_id = %s"
        self._execute_query(query, (user_id,))

    # ============================================================
    # LEARNING PATH OPERATIONS
    # ============================================================

    def save_learning_path(self, user_id: str, path_data: Dict[str, Any]) -> int:
        """
        Save learning path for a user

        Args:
            user_id: User UUID
            path_data: Full learning path output from Learning Path Agent

        Returns:
            Learning path ID
        """
        query = """
            INSERT INTO learning_paths (user_id, path_json)
            VALUES (%s, %s::jsonb)
            RETURNING id
        """
        result = self._execute_query(query, (user_id, json.dumps(path_data)), fetch_one=True)
        return result['id'] if result else None

    def get_learning_path(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get learning path for a user (most recent)

        Args:
            user_id: User UUID

        Returns:
            Learning path dict or None if not found
        """
        query = """
            SELECT path_json FROM learning_paths
            WHERE user_id = %s
            ORDER BY id DESC
            LIMIT 1
        """
        result = self._execute_query(query, (user_id,), fetch_one=True)
        return result['path_json'] if result else None

    def update_learning_path(self, user_id: str, path_data: Dict[str, Any]):
        """
        Update existing learning path for a user

        Args:
            user_id: User UUID
            path_data: Updated learning path data
        """
        query = """
            UPDATE learning_paths
            SET path_json = %s::jsonb, created_at = NOW()
            WHERE user_id = %s AND id = (
                SELECT id FROM learning_paths
                WHERE user_id = %s
                ORDER BY id DESC
                LIMIT 1
            )
        """
        self._execute_query(query, (json.dumps(path_data), user_id, user_id))

    def delete_user_learning_path(self, user_id: str):
        """
        Delete all learning paths for a user

        Args:
            user_id: User UUID
        """
        query = "DELETE FROM learning_paths WHERE user_id = %s"
        self._execute_query(query, (user_id,))

    # ============================================================
    # MODULE CHALLENGES OPERATIONS
    # ============================================================

    def save_module_challenges(
        self,
        user_id: str,
        module_number: int,
        challenges_data: Dict[str, Any]
    ) -> int:
        """
        Save challenges for a specific module

        Args:
            user_id: User UUID
            module_number: Module number (1-indexed)
            challenges_data: Full module challenges from Module Planner Agent

        Returns:
            Module challenges ID
        """
        query = """
            INSERT INTO module_challenges (user_id, module_number, challenges_json)
            VALUES (%s, %s, %s::jsonb)
            ON CONFLICT (user_id, module_number)
            DO UPDATE SET challenges_json = EXCLUDED.challenges_json
            RETURNING id
        """
        result = self._execute_query(
            query,
            (user_id, module_number, json.dumps(challenges_data)),
            fetch_one=True
        )
        return result['id'] if result else None

    def get_module_challenges(self, user_id: str, module_number: int) -> Optional[Dict[str, Any]]:
        """
        Get challenges for a specific module

        Args:
            user_id: User UUID
            module_number: Module number

        Returns:
            Module challenges dict or None if not found
        """
        query = """
            SELECT challenges_json FROM module_challenges
            WHERE user_id = %s AND module_number = %s
        """
        result = self._execute_query(query, (user_id, module_number), fetch_one=True)
        return result['challenges_json'] if result else None

    def get_all_module_challenges(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all module challenges for a user

        Args:
            user_id: User UUID

        Returns:
            List of module challenges dicts with module_number and challenges data
        """
        query = """
            SELECT module_number, challenges_json FROM module_challenges
            WHERE user_id = %s
            ORDER BY module_number
        """
        rows = self._execute_query(query, (user_id,), fetch_all=True)
        return [
            {
                'module_number': row['module_number'],
                **row['challenges_json']
            }
            for row in rows
        ]

    def delete_user_module_challenges(self, user_id: str):
        """
        Delete all module challenges for a user

        Args:
            user_id: User UUID
        """
        query = "DELETE FROM module_challenges WHERE user_id = %s"
        self._execute_query(query, (user_id,))

    # ============================================================
    # CHALLENGE PROGRESS OPERATIONS
    # ============================================================

    def create_challenge_progress(
        self,
        user_id: str,
        module_number: int,
        challenge_number: int,
        status: str = 'not_started'
    ) -> int:
        """
        Create a new challenge progress entry

        Args:
            user_id: User UUID
            module_number: Module number
            challenge_number: Challenge number within module
            status: not_started, in_progress, or completed

        Returns:
            Challenge progress ID
        """
        query = """
            INSERT INTO challenge_progress
            (user_id, module_number, challenge_number, status)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, module_number, challenge_number) DO NOTHING
            RETURNING id
        """
        result = self._execute_query(
            query,
            (user_id, module_number, challenge_number, status),
            fetch_one=True
        )
        return result['id'] if result else None

    def get_challenge_progress(
        self,
        user_id: str,
        module_number: int,
        challenge_number: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get progress for a specific challenge

        Args:
            user_id: User UUID
            module_number: Module number
            challenge_number: Challenge number

        Returns:
            Challenge progress dict or None if not found
        """
        query = """
            SELECT * FROM challenge_progress
            WHERE user_id = %s AND module_number = %s AND challenge_number = %s
        """
        return self._execute_query(query, (user_id, module_number, challenge_number), fetch_one=True)

    def update_challenge_status(
        self,
        user_id: str,
        module_number: int,
        challenge_number: int,
        status: str
    ):
        """
        Update challenge status

        Args:
            user_id: User UUID
            module_number: Module number
            challenge_number: Challenge number
            status: not_started, in_progress, or completed
        """
        query = """
            UPDATE challenge_progress
            SET status = %s, updated_at = NOW()
            WHERE user_id = %s AND module_number = %s AND challenge_number = %s
        """
        self._execute_query(query, (status, user_id, module_number, challenge_number))

    def complete_challenge(
        self,
        user_id: str,
        module_number: int,
        challenge_number: int
    ):
        """
        Mark a challenge as completed

        Args:
            user_id: User UUID
            module_number: Module number
            challenge_number: Challenge number
        """
        query = """
            UPDATE challenge_progress
            SET status = 'completed',
                completed_at = NOW(),
                updated_at = NOW()
            WHERE user_id = %s AND module_number = %s AND challenge_number = %s
        """
        self._execute_query(query, (user_id, module_number, challenge_number))

    def get_module_progress(self, user_id: str, module_number: int) -> List[Dict[str, Any]]:
        """
        Get progress for all challenges in a module

        Args:
            user_id: User UUID
            module_number: Module number

        Returns:
            List of challenge progress dicts
        """
        query = """
            SELECT * FROM challenge_progress
            WHERE user_id = %s AND module_number = %s
            ORDER BY challenge_number
        """
        return self._execute_query(query, (user_id, module_number), fetch_all=True)

    def get_all_progress(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get progress for all challenges across all modules

        Args:
            user_id: User UUID

        Returns:
            List of all challenge progress dicts
        """
        query = """
            SELECT * FROM challenge_progress
            WHERE user_id = %s
            ORDER BY module_number, challenge_number
        """
        return self._execute_query(query, (user_id,), fetch_all=True)

    def delete_user_progress(self, user_id: str):
        """
        Delete all challenge progress for a user

        Args:
            user_id: User UUID
        """
        query = "DELETE FROM challenge_progress WHERE user_id = %s"
        self._execute_query(query, (user_id,))

    def initialize_module_progress(self, user_id: str, module_number: int, num_challenges: int):
        """
        Create progress entries for all challenges in a module

        Args:
            user_id: User UUID
            module_number: Module number
            num_challenges: Total number of challenges in module
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self._get_connection() as conn:
                    with conn.cursor() as cur:
                        for i in range(1, num_challenges + 1):
                            cur.execute(
                                """INSERT INTO challenge_progress
                                   (user_id, module_number, challenge_number, status)
                                   VALUES (%s, %s, %s, %s)
                                   ON CONFLICT (user_id, module_number, challenge_number) DO NOTHING""",
                                (user_id, module_number, i, 'not_started')
                            )
                        conn.commit()
                return
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ Initialize progress error (attempt {attempt + 1}/{max_retries}): {e}")
                    continue
                raise

    def get_progress_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get overall progress summary for dashboard

        Args:
            user_id: User UUID

        Returns:
            Progress summary with counts by module, individual challenge status, and totals
        """
        # Get summary counts per module
        summary_query = """
            SELECT
                module_number,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'not_started' THEN 1 ELSE 0 END) as not_started
            FROM challenge_progress
            WHERE user_id = %s
            GROUP BY module_number
            ORDER BY module_number
        """
        summary = self._execute_query(summary_query, (user_id,), fetch_all=True)

        # Get individual challenge details
        details_query = """
            SELECT module_number, challenge_number, status
            FROM challenge_progress
            WHERE user_id = %s
            ORDER BY module_number, challenge_number
        """
        all_progress = self._execute_query(details_query, (user_id,), fetch_all=True)

        # Build challenge_details lookup by module
        challenge_details_by_module = {}
        for row in all_progress:
            module_num = row['module_number']
            challenge_num = row['challenge_number']
            if module_num not in challenge_details_by_module:
                challenge_details_by_module[module_num] = {}
            challenge_details_by_module[module_num][challenge_num] = {
                'status': row['status']
            }

        # Build modules list with challenge_details
        modules = []
        for row in summary:
            module_data = dict(row)
            module_data['challenge_details'] = challenge_details_by_module.get(row['module_number'], {})
            modules.append(module_data)

        total_completed = sum(row['completed'] for row in summary)
        total_challenges = sum(row['total'] for row in summary)

        return {
            'modules': modules,
            'total_completed': total_completed,
            'total_challenges': total_challenges,
            'completion_percentage': round((total_completed / total_challenges * 100) if total_challenges > 0 else 0, 1)
        }

    # ============================================================
    # TOKEN USAGE TRACKING (NEW - for cost monitoring)
    # ============================================================

    def log_token_usage(
        self,
        user_id: str,
        agent_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        model_name: str = None
    ):
        """
        Log token usage for cost tracking

        Args:
            user_id: User UUID
            agent_name: Name of the AI agent ('learning_path', 'module_planner', etc.)
            prompt_tokens: Input tokens
            completion_tokens: Output tokens
            total_tokens: Total tokens
            model_name: Model identifier
        """
        query = """
            INSERT INTO token_usage
            (user_id, agent_name, prompt_tokens, completion_tokens, total_tokens, model_name)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        self._execute_query(
            query,
            (user_id, agent_name, prompt_tokens, completion_tokens, total_tokens, model_name)
        )

    def get_user_token_usage(self, user_id: str) -> Dict[str, Any]:
        """
        Get token usage summary for a specific user

        Args:
            user_id: User UUID

        Returns:
            Dict with total tokens and breakdown by agent
        """
        query = """
            SELECT
                agent_name,
                model_name,
                SUM(prompt_tokens) as total_prompt_tokens,
                SUM(completion_tokens) as total_completion_tokens,
                SUM(total_tokens) as total_tokens,
                COUNT(*) as call_count
            FROM token_usage
            WHERE user_id = %s
            GROUP BY agent_name, model_name
            ORDER BY total_tokens DESC
        """
        breakdown = self._execute_query(query, (user_id,), fetch_all=True)

        total_query = """
            SELECT SUM(total_tokens) as grand_total
            FROM token_usage
            WHERE user_id = %s
        """
        total = self._execute_query(total_query, (user_id,), fetch_one=True)

        return {
            'total_tokens': total['grand_total'] or 0,
            'breakdown_by_agent': breakdown
        }

    # ============================================================
    # ADMIN OPERATIONS (NEW - for admin dashboard)
    # ============================================================

    def is_admin(self, user_id: str) -> bool:
        """
        Check if user is an admin

        Args:
            user_id: User UUID

        Returns:
            True if user is admin, False otherwise
        """
        query = "SELECT 1 FROM admin_users WHERE user_id = %s"
        result = self._execute_query(query, (user_id,), fetch_one=True)
        return result is not None

    def get_all_users_token_usage(self) -> List[Dict[str, Any]]:
        """
        Get token usage for all users (admin only)

        Returns:
            List of user token usage summaries with cost breakdown
        """
        query = """
            SELECT
                u.id as user_id,
                u.email,
                COALESCE(SUM(t.prompt_tokens), 0) as input_tokens,
                COALESCE(SUM(t.completion_tokens), 0) as output_tokens,
                COALESCE(SUM(t.total_tokens), 0) as total_tokens,
                COUNT(DISTINCT lp.id) as paths_created,
                COUNT(DISTINCT cp.id) FILTER (WHERE cp.status = 'completed') as lessons_completed,
                MAX(up.last_active) as last_active
            FROM auth.users u
            LEFT JOIN token_usage t ON u.id = t.user_id
            LEFT JOIN learning_paths lp ON u.id = lp.user_id
            LEFT JOIN user_profiles up ON u.id = up.user_id
            LEFT JOIN challenge_progress cp ON u.id = cp.user_id
            GROUP BY u.id, u.email
            ORDER BY total_tokens DESC
        """
        return self._execute_query(query, fetch_all=True)

    def get_admin_statistics(self) -> Dict[str, Any]:
        """
        Get aggregate statistics for admin dashboard

        Returns:
            Dict with total tokens, cost estimate, user breakdown, and daily usage
        """
        # Total token usage with input/output breakdown
        total_query = """
            SELECT
                COALESCE(SUM(prompt_tokens), 0) as total_input,
                COALESCE(SUM(completion_tokens), 0) as total_output,
                COALESCE(SUM(total_tokens), 0) as total
            FROM token_usage
        """
        total_result = self._execute_query(total_query, fetch_one=True)
        total_input_tokens = total_result['total_input'] or 0
        total_output_tokens = total_result['total_output'] or 0
        total_tokens = total_result['total'] or 0

        # Per-user breakdown
        users = self.get_all_users_token_usage()

        # Daily usage (last 30 days)
        daily_query = """
            SELECT
                DATE(created_at) as date,
                SUM(total_tokens) as tokens
            FROM token_usage
            WHERE created_at >= NOW() - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """
        daily_usage = self._execute_query(daily_query, fetch_all=True)

        # Calculate cost estimate
        # Gemini pricing: $0.50 per 1M input tokens, $3.00 per 1M output tokens
        input_cost = (total_input_tokens / 1_000_000) * 0.50
        output_cost = (total_output_tokens / 1_000_000) * 3.00
        estimated_cost = input_cost + output_cost

        return {
            'total_tokens': total_tokens,
            'total_input_tokens': total_input_tokens,
            'total_output_tokens': total_output_tokens,
            'estimated_cost': estimated_cost,
            'input_cost': input_cost,
            'output_cost': output_cost,
            'users': users,
            'daily_usage': [
                {
                    'date': str(row['date']),
                    'tokens': row['tokens'],
                    'percentage': (row['tokens'] / total_tokens * 100) if total_tokens > 0 else 0
                }
                for row in daily_usage
            ]
        }
