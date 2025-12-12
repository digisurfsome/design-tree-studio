"""
Roundtable Coder Service

Handles session, round, and agent management for multi-agent coding sessions.
Includes execution engine for calling AI models and calculating consensus.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.models import (
    RoundtableSession,
    RoundtableRound,
    RoundtableAgent,
    RoundtableResponse,
    RoundtableSessionStatus,
    AgentRole,
    VoteType,
)


# Available AI models for roundtable agents
AVAILABLE_MODELS = {
    # Anthropic
    "Opus 4.5": {
        "id": "claude-opus-4-5-20250101",
        "provider": "anthropic",
        "max_tokens": 200000,
    },
    "Sonnet 4.5": {
        "id": "claude-sonnet-4-5-20250929",
        "provider": "anthropic",
        "max_tokens": 200000,
    },
    "Sonnet 3.5": {
        "id": "claude-3-5-sonnet-20241022",
        "provider": "anthropic",
        "max_tokens": 200000,
    },
    # OpenAI
    "GPT-4 Turbo": {
        "id": "gpt-4-turbo-preview",
        "provider": "openai",
        "max_tokens": 128000,
    },
    "GPT-4o": {
        "id": "gpt-4o",
        "provider": "openai",
        "max_tokens": 128000,
    },
    "GPT-4o Mini": {
        "id": "gpt-4o-mini",
        "provider": "openai",
        "max_tokens": 128000,
    },
    "GPT-5.2": {
        "id": "gpt-5.2-2025-12-11",
        "provider": "openai",
        "max_tokens": 400000,
    },
}


# Agent role descriptions
AGENT_ROLES = {
    "builder": "Write code based on the task prompt",
    "voter": "Review code and vote approve/reject with explanation",
    "reviewer": "Provide detailed code review without voting",
}


# Default prompts
DEFAULT_SYSTEM_PROMPT = """You are an expert software developer. Write clean, well-documented code.
Follow best practices and handle errors appropriately."""

DEFAULT_VOTER_PROMPT_ADDITION = """Review the code provided by the builder.

Your response MUST start with one of:
- APPROVE: [your explanation]
- REJECT: [your explanation with specific issues]

Be specific about what's good or what needs fixing."""


class RoundtableService:
    """Service for managing roundtable coding sessions."""

    def __init__(
        self,
        db: Session,
        anthropic_key: Optional[str] = None,
        openai_key: Optional[str] = None,
    ):
        """
        Initialize the roundtable service.

        Args:
            db: SQLAlchemy database session
            anthropic_key: Anthropic API key (optional, for execution)
            openai_key: OpenAI API key (optional, for execution)
        """
        self.db = db
        self.anthropic_client = None
        self.openai_client = None

        if anthropic_key:
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
            except ImportError:
                pass

        if openai_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=openai_key)
            except ImportError:
                pass

    # =========================================================================
    # Session Management
    # =========================================================================

    def create_session(
        self,
        name: str,
        project_id: Optional[int] = None,
        master_prompt: Optional[str] = None,
        master_guardrails: Optional[str] = None,
        voting_threshold: float = 0.66,
        execution_mode: str = "single",
    ) -> RoundtableSession:
        """
        Create a new roundtable session.

        Args:
            name: Session name
            project_id: Optional project ID to link to
            master_prompt: Default system prompt for all agents
            master_guardrails: Guardrails to append to prompts
            voting_threshold: Required approval percentage (0.0-1.0)
            execution_mode: "single" or "multi"

        Returns:
            Created RoundtableSession
        """
        session = RoundtableSession(
            name=name,
            project_id=project_id,
            master_prompt=master_prompt or DEFAULT_SYSTEM_PROMPT,
            master_guardrails=master_guardrails,
            voting_threshold=voting_threshold,
            execution_mode=execution_mode,
            status=RoundtableSessionStatus.ACTIVE,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: int) -> Optional[RoundtableSession]:
        """
        Get a session by ID.

        Args:
            session_id: Session ID

        Returns:
            RoundtableSession or None
        """
        return self.db.query(RoundtableSession).filter(
            RoundtableSession.id == session_id
        ).first()

    def list_sessions(
        self,
        project_id: Optional[int] = None,
        status: Optional[RoundtableSessionStatus] = None,
    ) -> List[RoundtableSession]:
        """
        List all sessions, optionally filtered.

        Args:
            project_id: Filter by project ID
            status: Filter by status

        Returns:
            List of RoundtableSession objects
        """
        query = self.db.query(RoundtableSession)

        if project_id is not None:
            query = query.filter(RoundtableSession.project_id == project_id)
        if status is not None:
            query = query.filter(RoundtableSession.status == status)

        return query.order_by(RoundtableSession.updated_at.desc()).all()

    def update_session(
        self,
        session_id: int,
        **kwargs,
    ) -> Optional[RoundtableSession]:
        """
        Update session settings.

        Args:
            session_id: Session ID
            **kwargs: Fields to update (name, master_prompt, master_guardrails,
                     voting_threshold, execution_mode, status)

        Returns:
            Updated RoundtableSession or None
        """
        session = self.get_session(session_id)
        if not session:
            return None

        allowed_fields = {
            "name", "master_prompt", "master_guardrails",
            "voting_threshold", "execution_mode", "status", "project_id"
        }

        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(session, key, value)

        self.db.commit()
        self.db.refresh(session)
        return session

    def delete_session(self, session_id: int) -> bool:
        """
        Delete a session and all its rounds/agents/responses.

        Args:
            session_id: Session ID

        Returns:
            True if deleted, False if not found
        """
        session = self.get_session(session_id)
        if not session:
            return False

        self.db.delete(session)
        self.db.commit()
        return True

    # =========================================================================
    # Round Management
    # =========================================================================

    def add_round(
        self,
        session_id: int,
        name: Optional[str] = None,
        task_prompt: Optional[str] = None,
    ) -> Optional[RoundtableRound]:
        """
        Add a round to a session.

        Args:
            session_id: Session ID
            name: Optional round name
            task_prompt: Task/instructions for the round

        Returns:
            Created RoundtableRound or None if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return None

        # Get next round number
        max_round = self.db.query(func.max(RoundtableRound.round_number)).filter(
            RoundtableRound.session_id == session_id
        ).scalar() or 0

        round_obj = RoundtableRound(
            session_id=session_id,
            round_number=max_round + 1,
            name=name or f"Round {max_round + 1}",
            task_prompt=task_prompt,
            status="pending",
        )
        self.db.add(round_obj)
        self.db.commit()
        self.db.refresh(round_obj)
        return round_obj

    def get_round(self, round_id: int) -> Optional[RoundtableRound]:
        """
        Get a round by ID.

        Args:
            round_id: Round ID

        Returns:
            RoundtableRound or None
        """
        return self.db.query(RoundtableRound).filter(
            RoundtableRound.id == round_id
        ).first()

    def list_rounds(self, session_id: int) -> List[RoundtableRound]:
        """
        List all rounds for a session.

        Args:
            session_id: Session ID

        Returns:
            List of RoundtableRound objects ordered by round_number
        """
        return self.db.query(RoundtableRound).filter(
            RoundtableRound.session_id == session_id
        ).order_by(RoundtableRound.round_number).all()

    def update_round(
        self,
        round_id: int,
        **kwargs,
    ) -> Optional[RoundtableRound]:
        """
        Update round settings.

        Args:
            round_id: Round ID
            **kwargs: Fields to update (name, task_prompt, status)

        Returns:
            Updated RoundtableRound or None
        """
        round_obj = self.get_round(round_id)
        if not round_obj:
            return None

        allowed_fields = {"name", "task_prompt", "status"}

        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(round_obj, key, value)

        self.db.commit()
        self.db.refresh(round_obj)
        return round_obj

    def delete_round(self, round_id: int) -> bool:
        """
        Delete a round and all its agents/responses.

        Args:
            round_id: Round ID

        Returns:
            True if deleted, False if not found
        """
        round_obj = self.get_round(round_id)
        if not round_obj:
            return False

        self.db.delete(round_obj)
        self.db.commit()
        return True

    # =========================================================================
    # Agent Management
    # =========================================================================

    def add_agent(
        self,
        round_id: int,
        model_name: str,
        role: str,
        prompt_override: Optional[str] = None,
    ) -> Optional[RoundtableAgent]:
        """
        Add an agent to a round.

        Args:
            round_id: Round ID
            model_name: Model name (key from AVAILABLE_MODELS)
            role: Agent role ("builder", "voter", "reviewer")
            prompt_override: Custom prompt for this agent

        Returns:
            Created RoundtableAgent or None if round not found or invalid model
        """
        round_obj = self.get_round(round_id)
        if not round_obj:
            return None

        if model_name not in AVAILABLE_MODELS:
            return None

        model_info = AVAILABLE_MODELS[model_name]

        # Get next agent order
        max_order = self.db.query(func.max(RoundtableAgent.agent_order)).filter(
            RoundtableAgent.round_id == round_id
        ).scalar() or -1

        agent = RoundtableAgent(
            round_id=round_id,
            agent_order=max_order + 1,
            model=model_info["id"],
            provider=model_info["provider"],
            role=AgentRole(role),
            prompt_override=prompt_override,
        )
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def get_agent(self, agent_id: int) -> Optional[RoundtableAgent]:
        """
        Get an agent by ID.

        Args:
            agent_id: Agent ID

        Returns:
            RoundtableAgent or None
        """
        return self.db.query(RoundtableAgent).filter(
            RoundtableAgent.id == agent_id
        ).first()

    def list_agents(self, round_id: int) -> List[RoundtableAgent]:
        """
        List all agents for a round.

        Args:
            round_id: Round ID

        Returns:
            List of RoundtableAgent objects ordered by agent_order
        """
        return self.db.query(RoundtableAgent).filter(
            RoundtableAgent.round_id == round_id
        ).order_by(RoundtableAgent.agent_order).all()

    def update_agent(
        self,
        agent_id: int,
        **kwargs,
    ) -> Optional[RoundtableAgent]:
        """
        Update agent configuration.

        Args:
            agent_id: Agent ID
            **kwargs: Fields to update (model_name, role, prompt_override, agent_order)

        Returns:
            Updated RoundtableAgent or None
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return None

        # Handle model_name specially (need to look up model info)
        if "model_name" in kwargs:
            model_name = kwargs.pop("model_name")
            if model_name in AVAILABLE_MODELS:
                model_info = AVAILABLE_MODELS[model_name]
                agent.model = model_info["id"]
                agent.provider = model_info["provider"]

        # Handle role specially (convert string to enum)
        if "role" in kwargs:
            role_str = kwargs.pop("role")
            agent.role = AgentRole(role_str)

        allowed_fields = {"prompt_override", "agent_order"}

        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(agent, key, value)

        self.db.commit()
        self.db.refresh(agent)
        return agent

    def delete_agent(self, agent_id: int) -> bool:
        """
        Delete an agent and all its responses.

        Args:
            agent_id: Agent ID

        Returns:
            True if deleted, False if not found
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        self.db.delete(agent)
        self.db.commit()
        return True

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_model_display_name(self, model_id: str) -> str:
        """
        Get display name for a model ID.

        Args:
            model_id: Model ID (e.g., "claude-opus-4-5-20250101")

        Returns:
            Display name (e.g., "Opus 4.5") or the model_id if not found
        """
        for name, info in AVAILABLE_MODELS.items():
            if info["id"] == model_id:
                return name
        return model_id

    def get_session_stats(self, session_id: int) -> Dict[str, Any]:
        """
        Get statistics for a session.

        Args:
            session_id: Session ID

        Returns:
            Dictionary with session statistics
        """
        session = self.get_session(session_id)
        if not session:
            return {}

        rounds = self.list_rounds(session_id)

        total_rounds = len(rounds)
        completed_rounds = sum(1 for r in rounds if r.status == "completed")
        pending_rounds = sum(1 for r in rounds if r.status == "pending")

        # Calculate total cost and tokens across all responses
        total_cost = 0.0
        total_tokens_in = 0
        total_tokens_out = 0

        for round_obj in rounds:
            for agent in round_obj.agents:
                for response in agent.responses:
                    total_cost += response.cost
                    total_tokens_in += response.tokens_input
                    total_tokens_out += response.tokens_output

        return {
            "total_rounds": total_rounds,
            "completed_rounds": completed_rounds,
            "pending_rounds": pending_rounds,
            "total_cost": total_cost,
            "total_tokens_in": total_tokens_in,
            "total_tokens_out": total_tokens_out,
        }

    # =========================================================================
    # Execution Engine
    # =========================================================================

    def call_agent(
        self,
        agent: RoundtableAgent,
        system_prompt: str,
        user_prompt: str,
        iteration: int = 1,
    ) -> RoundtableResponse:
        """
        Make API call to a single agent and store response.

        Args:
            agent: RoundtableAgent to call
            system_prompt: System prompt for the model
            user_prompt: User message/task
            iteration: Iteration number (for revisions)

        Returns:
            RoundtableResponse with results

        Raises:
            ValueError: If no API client available for provider
            Exception: If API call fails
        """
        import time

        start_time = time.time()
        content = ""
        tokens_in = 0
        tokens_out = 0
        cost = 0.0

        if agent.provider == "anthropic":
            if not self.anthropic_client:
                raise ValueError("Anthropic client not configured. Please set API key.")

            response = self.anthropic_client.messages.create(
                model=agent.model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            content = response.content[0].text
            tokens_in = response.usage.input_tokens
            tokens_out = response.usage.output_tokens

            # Estimate cost (Opus 4 pricing: $15/1M in, $75/1M out)
            if "opus" in agent.model.lower():
                cost = (tokens_in * 15 / 1_000_000) + (tokens_out * 75 / 1_000_000)
            else:  # Sonnet pricing: $3/1M in, $15/1M out
                cost = (tokens_in * 3 / 1_000_000) + (tokens_out * 15 / 1_000_000)

        elif agent.provider == "openai":
            if not self.openai_client:
                raise ValueError("OpenAI client not configured. Please set API key.")

            response = self.openai_client.chat.completions.create(
                model=agent.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content
            tokens_in = response.usage.prompt_tokens
            tokens_out = response.usage.completion_tokens

            # Estimate cost (GPT-4 pricing varies)
            if "gpt-4o-mini" in agent.model:
                cost = (tokens_in * 0.15 / 1_000_000) + (tokens_out * 0.6 / 1_000_000)
            elif "gpt-4o" in agent.model:
                cost = (tokens_in * 5 / 1_000_000) + (tokens_out * 15 / 1_000_000)
            elif "gpt-5" in agent.model:
                cost = (tokens_in * 10 / 1_000_000) + (tokens_out * 30 / 1_000_000)
            else:  # GPT-4 Turbo
                cost = (tokens_in * 10 / 1_000_000) + (tokens_out * 30 / 1_000_000)
        else:
            raise ValueError(f"Unknown provider: {agent.provider}")

        duration = time.time() - start_time

        # Parse vote if this is a voter agent
        vote = None
        vote_reason = None
        if agent.role == AgentRole.VOTER:
            vote, vote_reason = self._parse_vote(content)

        # Create and store response
        response_obj = RoundtableResponse(
            agent_id=agent.id,
            iteration=iteration,
            content=content,
            vote=vote,
            vote_reason=vote_reason,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            cost=cost,
            duration_seconds=duration,
        )
        self.db.add(response_obj)
        self.db.commit()
        self.db.refresh(response_obj)

        return response_obj

    def _parse_vote(self, content: str) -> tuple[Optional[VoteType], Optional[str]]:
        """
        Parse a voter's response to extract vote and reason.

        Args:
            content: Response content from voter

        Returns:
            Tuple of (VoteType, reason) or (None, None) if not parseable
        """
        if not content:
            return None, None

        content_upper = content.strip().upper()

        if content_upper.startswith("APPROVE"):
            reason = content[len("APPROVE"):].strip()
            if reason.startswith(":"):
                reason = reason[1:].strip()
            return VoteType.APPROVE, reason or "Approved"

        elif content_upper.startswith("REJECT"):
            reason = content[len("REJECT"):].strip()
            if reason.startswith(":"):
                reason = reason[1:].strip()
            return VoteType.REJECT, reason or "Rejected"

        elif content_upper.startswith("ABSTAIN"):
            reason = content[len("ABSTAIN"):].strip()
            if reason.startswith(":"):
                reason = reason[1:].strip()
            return VoteType.ABSTAIN, reason or "Abstained"

        # Try to infer from content
        if "approve" in content.lower()[:100]:
            return VoteType.APPROVE, content
        elif "reject" in content.lower()[:100]:
            return VoteType.REJECT, content

        return VoteType.ABSTAIN, content

    def execute_round(
        self,
        round_id: int,
        execution_mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute all agents in a round.

        Args:
            round_id: Round ID to execute
            execution_mode: Override execution mode ("single" or "multi")
                           If None, uses session's execution_mode

        Returns:
            Dictionary with execution results:
            {
                "success": bool,
                "error": str or None,
                "builder_response": RoundtableResponse or None,
                "voter_responses": List[RoundtableResponse],
                "consensus": dict from calculate_consensus()
            }
        """
        round_obj = self.get_round(round_id)
        if not round_obj:
            return {"success": False, "error": "Round not found"}

        session = round_obj.session
        mode = execution_mode or session.execution_mode

        # Mark round as running
        round_obj.status = "running"
        self.db.commit()

        agents = self.list_agents(round_id)
        if not agents:
            round_obj.status = "pending"
            self.db.commit()
            return {"success": False, "error": "No agents configured for this round"}

        # Build prompts
        system_prompt = session.master_prompt or DEFAULT_SYSTEM_PROMPT
        if session.master_guardrails:
            system_prompt = f"{system_prompt}\n\n{session.master_guardrails}"

        user_prompt = round_obj.task_prompt or "No task specified."

        result = {
            "success": True,
            "error": None,
            "builder_response": None,
            "voter_responses": [],
            "consensus": None,
        }

        try:
            # Find builder agent
            builder = None
            voters = []
            for agent in agents:
                if agent.role == AgentRole.BUILDER:
                    builder = agent
                elif agent.role == AgentRole.VOTER:
                    voters.append(agent)

            # Single mode: only run builder
            if mode == "single":
                if builder:
                    agent_prompt = builder.prompt_override or system_prompt
                    response = self.call_agent(builder, agent_prompt, user_prompt)
                    result["builder_response"] = response
                elif agents:
                    # Use first agent as builder if no builder role assigned
                    agent = agents[0]
                    agent_prompt = agent.prompt_override or system_prompt
                    response = self.call_agent(agent, agent_prompt, user_prompt)
                    result["builder_response"] = response

            # Multi mode: run builder then voters
            elif mode == "multi":
                builder_content = ""

                # Run builder first
                if builder:
                    agent_prompt = builder.prompt_override or system_prompt
                    builder_response = self.call_agent(builder, agent_prompt, user_prompt)
                    result["builder_response"] = builder_response
                    builder_content = builder_response.content

                # Run voters with builder's output
                if voters and builder_content:
                    voter_prompt = f"""{user_prompt}

---
BUILDER'S CODE/RESPONSE:
---
{builder_content}
---

{DEFAULT_VOTER_PROMPT_ADDITION}"""

                    for voter in voters:
                        voter_system = voter.prompt_override or system_prompt
                        voter_response = self.call_agent(voter, voter_system, voter_prompt)
                        result["voter_responses"].append(voter_response)

                # Calculate consensus
                result["consensus"] = self.calculate_consensus(round_id)

            # Mark round complete
            round_obj.status = "completed"
            round_obj.completed_at = datetime.utcnow()

            if result["consensus"]:
                round_obj.consensus_reached = result["consensus"]["passed"]
                round_obj.consensus_percentage = result["consensus"]["percentage"]

            self.db.commit()

        except Exception as e:
            round_obj.status = "pending"
            self.db.commit()
            result["success"] = False
            result["error"] = str(e)

        return result

    def calculate_consensus(self, round_id: int) -> Dict[str, Any]:
        """
        Calculate voting consensus for a round.

        Args:
            round_id: Round ID

        Returns:
            Dictionary with consensus info:
            {
                "total_voters": int,
                "approvals": int,
                "rejections": int,
                "abstentions": int,
                "percentage": float (0.0-1.0),
                "threshold": float,
                "passed": bool,
                "feedback": list[str]
            }
        """
        round_obj = self.get_round(round_id)
        if not round_obj:
            return {
                "total_voters": 0,
                "approvals": 0,
                "rejections": 0,
                "abstentions": 0,
                "percentage": 0.0,
                "threshold": 0.66,
                "passed": False,
                "feedback": [],
            }

        session = round_obj.session
        threshold = session.voting_threshold

        # Get latest responses from voter agents
        voters = [a for a in round_obj.agents if a.role == AgentRole.VOTER]

        total_voters = 0
        approvals = 0
        rejections = 0
        abstentions = 0
        feedback = []

        for voter in voters:
            # Get most recent response
            if voter.responses:
                latest = max(voter.responses, key=lambda r: r.iteration)
                total_voters += 1

                if latest.vote == VoteType.APPROVE:
                    approvals += 1
                elif latest.vote == VoteType.REJECT:
                    rejections += 1
                    if latest.vote_reason:
                        feedback.append(latest.vote_reason)
                else:
                    abstentions += 1

        # Calculate percentage (excluding abstentions)
        voting_total = approvals + rejections
        percentage = approvals / voting_total if voting_total > 0 else 0.0
        passed = percentage >= threshold

        return {
            "total_voters": total_voters,
            "approvals": approvals,
            "rejections": rejections,
            "abstentions": abstentions,
            "percentage": percentage,
            "threshold": threshold,
            "passed": passed,
            "feedback": feedback,
        }

    def get_round_responses(self, round_id: int) -> Dict[str, Any]:
        """
        Get all responses for a round, organized by agent.

        Args:
            round_id: Round ID

        Returns:
            Dictionary with responses organized by role:
            {
                "builder": RoundtableResponse or None,
                "voters": List[dict with agent info and response],
                "reviewers": List[dict with agent info and response]
            }
        """
        round_obj = self.get_round(round_id)
        if not round_obj:
            return {"builder": None, "voters": [], "reviewers": []}

        result = {"builder": None, "voters": [], "reviewers": []}

        for agent in round_obj.agents:
            # Get latest response
            latest_response = None
            if agent.responses:
                latest_response = max(agent.responses, key=lambda r: r.iteration)

            agent_info = {
                "agent_id": agent.id,
                "model": agent.model,
                "model_name": self.get_model_display_name(agent.model),
                "provider": agent.provider,
                "response": latest_response,
            }

            if agent.role == AgentRole.BUILDER:
                result["builder"] = agent_info
            elif agent.role == AgentRole.VOTER:
                result["voters"].append(agent_info)
            elif agent.role == AgentRole.REVIEWER:
                result["reviewers"].append(agent_info)

        return result
