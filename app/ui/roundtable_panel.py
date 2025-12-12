"""
Roundtable Coder UI Panel

Main UI for the multi-agent roundtable coding system.
"""

import streamlit as st
from typing import Optional
from sqlalchemy.orm import Session as DBSession

from app.core.models import Project, RoundtableSessionStatus, AgentRole
from app.services.roundtable_service import (
    RoundtableService,
    AVAILABLE_MODELS,
    AGENT_ROLES,
    DEFAULT_SYSTEM_PROMPT,
)
from app.services import get_setting


def render_roundtable_panel(db: DBSession, project: Optional[Project] = None) -> None:
    """
    Render the main Roundtable Coder panel.

    Args:
        db: Database session
        project: Optional current project for linking sessions
    """
    st.header("Roundtable Coder")
    st.markdown("*Multi-agent coding with consensus voting*")

    # Get API keys from settings
    anthropic_key = get_setting(db, "ANTHROPIC_API_KEY")
    openai_key = get_setting(db, "OPENAI_API_KEY")

    # Initialize service
    service = RoundtableService(
        db=db,
        anthropic_key=anthropic_key,
        openai_key=openai_key,
    )

    # Check for API keys
    if not anthropic_key and not openai_key:
        st.warning("No API keys configured. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY in Settings tab.")

    # Initialize session state
    if "roundtable_session_id" not in st.session_state:
        st.session_state.roundtable_session_id = None

    # =========================================================================
    # Session Management
    # =========================================================================
    st.subheader("Session")

    col1, col2, col3 = st.columns([3, 1, 1])

    # Get all sessions
    sessions = service.list_sessions(project_id=project.id if project else None)

    with col1:
        # Session selector
        session_options = ["-- Create New --"] + [f"{s.name} (#{s.id})" for s in sessions]
        session_names = {f"{s.name} (#{s.id})": s.id for s in sessions}

        selected = st.selectbox(
            "Select Session",
            session_options,
            key="roundtable_session_selector",
        )

        if selected != "-- Create New --":
            st.session_state.roundtable_session_id = session_names.get(selected)
        else:
            st.session_state.roundtable_session_id = None

    with col2:
        if st.button("+ New", use_container_width=True, key="rt_new_session"):
            st.session_state.show_create_session = True
            st.rerun()

    with col3:
        if st.session_state.roundtable_session_id:
            if st.button("Delete", use_container_width=True, type="secondary", key="rt_delete_session"):
                service.delete_session(st.session_state.roundtable_session_id)
                st.session_state.roundtable_session_id = None
                st.success("Session deleted!")
                st.rerun()

    # Create session form
    if st.session_state.get("show_create_session", False):
        with st.expander("Create New Session", expanded=True):
            new_name = st.text_input("Session Name", placeholder="My Roundtable Session")
            if st.button("Create Session", type="primary"):
                if new_name:
                    new_session = service.create_session(
                        name=new_name,
                        project_id=project.id if project else None,
                    )
                    st.session_state.roundtable_session_id = new_session.id
                    st.session_state.show_create_session = False
                    st.success(f"Created session: {new_name}")
                    st.rerun()
                else:
                    st.error("Please enter a session name")

            if st.button("Cancel"):
                st.session_state.show_create_session = False
                st.rerun()

    # =========================================================================
    # Session Configuration (if session selected)
    # =========================================================================
    if st.session_state.roundtable_session_id:
        session = service.get_session(st.session_state.roundtable_session_id)
        if not session:
            st.error("Session not found")
            return

        st.divider()

        # Execution Mode Toggle - CRITICAL
        st.subheader("Execution Mode")

        col1, col2 = st.columns(2)

        with col1:
            mode = st.radio(
                "Mode",
                ["single", "multi"],
                index=0 if session.execution_mode == "single" else 1,
                format_func=lambda x: "Single Agent (Builder only)" if x == "single" else "Multi-Agent (Builder + Voters)",
                key="rt_execution_mode",
                horizontal=True,
            )

            if mode != session.execution_mode:
                service.update_session(session.id, execution_mode=mode)
                st.rerun()

        with col2:
            # Voting threshold slider (only show in multi mode)
            if mode == "multi":
                threshold = st.slider(
                    "Voting Threshold",
                    min_value=50,
                    max_value=100,
                    value=int(session.voting_threshold * 100),
                    step=5,
                    format="%d%%",
                    help="Required approval percentage for consensus",
                    key="rt_threshold",
                )

                if threshold / 100 != session.voting_threshold:
                    service.update_session(session.id, voting_threshold=threshold / 100)
                    st.rerun()

        # Master prompt (collapsible)
        with st.expander("Master Prompt & Guardrails"):
            master_prompt = st.text_area(
                "System Prompt (for all agents)",
                value=session.master_prompt or DEFAULT_SYSTEM_PROMPT,
                height=100,
                key="rt_master_prompt",
            )

            guardrails = st.text_area(
                "Guardrails (appended to prompt)",
                value=session.master_guardrails or "",
                height=100,
                placeholder="Additional rules or constraints...",
                key="rt_guardrails",
            )

            if st.button("Save Prompts"):
                service.update_session(
                    session.id,
                    master_prompt=master_prompt,
                    master_guardrails=guardrails,
                )
                st.success("Prompts saved!")

        # =====================================================================
        # Rounds Management
        # =====================================================================
        st.divider()
        st.subheader("Rounds")

        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("+ Add Round", key="rt_add_round"):
                service.add_round(session.id, name=f"Round {len(session.rounds) + 1}")
                st.rerun()

        # List rounds
        rounds = service.list_rounds(session.id)

        if not rounds:
            st.info("No rounds yet. Click '+ Add Round' to create one.")
        else:
            for round_obj in rounds:
                _render_round_card(service, round_obj, mode)

        # =====================================================================
        # Execution Panel
        # =====================================================================
        render_execution_panel(db, service, session)

    else:
        st.info("Select or create a session to get started.")


def _render_round_card(service: RoundtableService, round_obj, execution_mode: str) -> None:
    """Render a single round card with agents."""
    with st.expander(f"{round_obj.name} - {round_obj.status}", expanded=True):
        # Round task prompt
        col1, col2 = st.columns([5, 1])

        with col1:
            task = st.text_area(
                "Task Prompt",
                value=round_obj.task_prompt or "",
                height=80,
                placeholder="What should the builder create?",
                key=f"rt_task_{round_obj.id}",
            )

            if task != (round_obj.task_prompt or ""):
                service.update_round(round_obj.id, task_prompt=task)

        with col2:
            st.write("")  # Spacer
            st.write("")
            if st.button("Delete", key=f"rt_del_round_{round_obj.id}", type="secondary"):
                service.delete_round(round_obj.id)
                st.rerun()

        # Agents
        st.markdown("**Agents:**")

        agents = service.list_agents(round_obj.id)

        # Add agent button
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

        with col1:
            new_model = st.selectbox(
                "Model",
                list(AVAILABLE_MODELS.keys()),
                key=f"rt_new_agent_model_{round_obj.id}",
                label_visibility="collapsed",
            )

        with col2:
            role_options = ["builder", "voter", "reviewer"]
            new_role = st.selectbox(
                "Role",
                role_options,
                key=f"rt_new_agent_role_{round_obj.id}",
                label_visibility="collapsed",
            )

        with col3:
            st.text("")  # Alignment spacer

        with col4:
            if st.button("+ Add", key=f"rt_add_agent_{round_obj.id}"):
                service.add_agent(round_obj.id, new_model, new_role)
                st.rerun()

        # List existing agents
        if agents:
            for agent in agents:
                _render_agent_row(service, agent)
        else:
            st.caption("No agents added yet.")


def _render_agent_row(service: RoundtableService, agent) -> None:
    """Render a single agent row."""
    col1, col2, col3, col4 = st.columns([1, 3, 2, 1])

    with col1:
        st.markdown(f"**{agent.agent_order + 1}.**")

    with col2:
        model_name = service.get_model_display_name(agent.model)
        provider_badge = "Anthropic" if agent.provider == "anthropic" else "OpenAI"
        st.markdown(f"{model_name} ({provider_badge})")

    with col3:
        role_emoji = ""
        if agent.role == AgentRole.BUILDER:
            role_emoji = "Builder"
        elif agent.role == AgentRole.VOTER:
            role_emoji = "Voter"
        else:
            role_emoji = "Reviewer"
        st.markdown(role_emoji)

    with col4:
        if st.button("X", key=f"rt_del_agent_{agent.id}"):
            service.delete_agent(agent.id)
            st.rerun()


def render_execution_panel(db: DBSession, service: RoundtableService, session) -> None:
    """
    Render the execution controls and results panel.

    Args:
        db: Database session
        service: RoundtableService instance
        session: Current RoundtableSession
    """
    st.divider()
    st.subheader("Execution")

    rounds = service.list_rounds(session.id)

    if not rounds:
        st.info("Add a round first before executing.")
        return

    # Round selector
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        round_options = {f"{r.name} (#{r.id})": r.id for r in rounds}
        selected_round = st.selectbox(
            "Select Round to Execute",
            list(round_options.keys()),
            key="rt_exec_round",
        )
        selected_round_id = round_options.get(selected_round)

    # Check if round has agents
    round_obj = service.get_round(selected_round_id) if selected_round_id else None
    agents = service.list_agents(selected_round_id) if selected_round_id else []

    with col2:
        run_disabled = not agents or not round_obj or round_obj.status == "running"
        if st.button("Run Round", type="primary", disabled=run_disabled, key="rt_run"):
            if selected_round_id:
                _execute_round(service, selected_round_id)
                st.rerun()

    with col3:
        if st.button("Re-run", disabled=run_disabled, key="rt_rerun"):
            if selected_round_id:
                _execute_round(service, selected_round_id)
                st.rerun()

    # Status
    if round_obj:
        status_color = {
            "pending": "gray",
            "running": "blue",
            "completed": "green",
        }.get(round_obj.status, "gray")

        st.markdown(f"**Status:** :{status_color}[{round_obj.status.upper()}]")

        # Show results if completed
        if round_obj.status == "completed":
            _render_results(service, round_obj.id, session.execution_mode)


def _execute_round(service: RoundtableService, round_id: int) -> None:
    """Execute a round and show progress."""
    with st.spinner("Executing round..."):
        result = service.execute_round(round_id)

        if result["success"]:
            st.success("Round executed successfully!")
        else:
            st.error(f"Execution failed: {result['error']}")


def _render_results(service: RoundtableService, round_id: int, execution_mode: str) -> None:
    """Render execution results for a round."""
    st.divider()
    st.subheader("Results")

    responses = service.get_round_responses(round_id)

    # Builder response
    builder_info = responses.get("builder")
    if builder_info and builder_info.get("response"):
        response = builder_info["response"]

        st.markdown(f"### Builder ({builder_info['model_name']})")

        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Tokens", f"{response.tokens_input + response.tokens_output:,}")
        with col2:
            st.metric("Cost", f"${response.cost:.4f}")
        with col3:
            st.metric("Time", f"{response.duration_seconds:.1f}s")

        # Content
        with st.expander("View Response", expanded=True):
            st.code(response.content, language="python")

        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("Copy", key="rt_copy_builder"):
                st.toast("Copied to clipboard!")

    # Voter responses (only in multi mode)
    if execution_mode == "multi":
        voters = responses.get("voters", [])

        if voters:
            st.divider()
            st.markdown("### Voter Responses")

            for i, voter_info in enumerate(voters):
                response = voter_info.get("response")
                if response:
                    # Vote indicator
                    vote_emoji = ""
                    if response.vote:
                        if response.vote.value == "approve":
                            vote_emoji = "APPROVE"
                        elif response.vote.value == "reject":
                            vote_emoji = "REJECT"
                        else:
                            vote_emoji = "ABSTAIN"

                    st.markdown(f"**Voter {i+1}** ({voter_info['model_name']}) - **{vote_emoji}**")

                    # Metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.caption(f"Tokens: {response.tokens_input + response.tokens_output:,}")
                    with col2:
                        st.caption(f"Cost: ${response.cost:.4f}")
                    with col3:
                        st.caption(f"Time: {response.duration_seconds:.1f}s")

                    with st.expander("View Response"):
                        st.markdown(response.content)

            # Consensus
            st.divider()
            consensus = service.calculate_consensus(round_id)

            if consensus["total_voters"] > 0:
                percentage = consensus["percentage"] * 100
                threshold = consensus["threshold"] * 100

                status = "PASSED" if consensus["passed"] else "FAILED"
                status_color = "green" if consensus["passed"] else "red"

                st.markdown(
                    f"### Consensus: {consensus['approvals']}/{consensus['total_voters']} "
                    f"approved ({percentage:.0f}%) - :{status_color}[{status}]"
                )

                st.progress(consensus["percentage"])
                st.caption(f"Threshold: {threshold:.0f}%")

                # Feedback from rejections
                if consensus["feedback"]:
                    with st.expander("Rejection Feedback"):
                        for fb in consensus["feedback"]:
                            st.markdown(f"- {fb[:500]}...")  # Truncate long feedback
