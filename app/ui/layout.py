"""
UI layout components and helpers for Streamlit.

This module provides reusable UI components and layout functions.
"""

import streamlit as st
from typing import Optional, List, Tuple, Dict
from sqlalchemy.orm import Session

from app.core.models import UserProfile, Project, DescriptionMode
from app.services import (
    list_all_users,
    list_user_projects,
    create_project,
    get_all_settings,
    set_multiple_settings,
    get_project_context,
    update_project_context,
    get_or_create_chat_session,
    get_chat_history,
    send_chat_message,
    clear_chat_history,
    get_token_usage,
    get_setting_as_int,
    generate_baton,
    check_auto_baton_trigger,
    get_warmed_sessions,
    switch_to_session,
    generate_auto_project_description,
    get_combined_description,
    update_description_mode,
    export_truth_doc,
    get_truth_doc_filename,
    get_truth_doc_preview,
    detect_nodes_from_exchange,
    get_node_type_icon,
    create_node,
)
from app.core.models import NodeType, NodeStatus


def inject_compact_css() -> None:
    """
    Inject CSS to create a compact, space-efficient layout.
    Reduces Streamlit's default padding and margins.
    """
    st.markdown("""
    <style>
    /* Reduce main container padding */
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }

    /* Reduce header padding */
    header[data-testid="stHeader"] {
        height: 2.5rem !important;
    }

    /* Tighter tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        padding: 0;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 12px !important;
        font-size: 13px !important;
    }

    /* Reduce spacing in columns */
    [data-testid="column"] {
        padding: 0 8px !important;
    }

    /* Compact sidebar */
    [data-testid="stSidebar"] {
        min-width: 200px !important;
        max-width: 250px !important;
    }
    [data-testid="stSidebar"] .block-container {
        padding: 1rem 0.5rem !important;
    }

    /* Reduce vertical spacing between elements */
    .element-container {
        margin-bottom: 0.5rem !important;
    }

    /* Compact expander */
    .streamlit-expanderHeader {
        padding: 0.5rem !important;
        font-size: 14px !important;
    }

    /* Tighter form elements */
    .stTextInput, .stSelectbox, .stTextArea {
        margin-bottom: 0.5rem !important;
    }

    /* Compact status bar */
    .compact-status-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 16px;
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 8px;
        margin-bottom: 8px;
        gap: 12px;
        flex-wrap: wrap;
    }
    .compact-status-bar .status-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 13px;
        color: #e2e8f0;
    }
    .compact-status-bar .status-badge {
        padding: 3px 10px;
        border-radius: 10px;
        font-size: 11px;
        font-weight: 600;
    }
    .badge-green { background: #059669; color: white; }
    .badge-yellow { background: #d97706; color: #1e293b; }
    .badge-blue { background: #3b82f6; color: white; }
    .badge-purple { background: #8b5cf6; color: white; }

    /* Inline refresh banner */
    .inline-refresh-banner {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 16px;
        background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%);
        border: 1px solid #3b82f6;
        border-radius: 8px;
        margin-bottom: 8px;
    }
    .inline-refresh-banner .refresh-text {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #e2e8f0;
        font-size: 13px;
    }
    .inline-refresh-banner .time-badge {
        background: rgba(59, 130, 246, 0.3);
        padding: 2px 8px;
        border-radius: 8px;
        font-size: 11px;
        color: #93c5fd;
    }

    /* Hide default Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Compact project banner */
    .project-banner {
        background: linear-gradient(135deg, #065f46 0%, #064e3b 100%);
        padding: 8px 12px;
        border-radius: 6px;
        margin-bottom: 8px;
        font-size: 13px;
        color: #d1fae5;
    }
    </style>
    """, unsafe_allow_html=True)


def render_compact_status_bar(
    project_name: str,
    is_ready: bool = True,
    ideas_count: int = 0,
    time_away_str: Optional[str] = None,
) -> None:
    """
    Render a single-row compact status bar with all key info.
    Uses native Streamlit components for reliability.
    """
    # Use columns for horizontal layout
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        st.markdown(f"📁 **{project_name}**")

    with col2:
        if time_away_str:
            st.caption(f"Away {time_away_str}")

    with col3:
        if is_ready:
            st.success("Ready", icon="✓")
        else:
            st.warning("Warmup", icon="⏳")

    with col4:
        st.caption(f"💡 {ideas_count} ideas")


def render_header(title: str, subtitle: Optional[str] = None) -> None:
    """
    Render application header.
    NOTE: This is the OLD header - use inject_compact_css() + render_compact_status_bar() instead.

    Args:
        title: Main title
        subtitle: Optional subtitle
    """
    st.title(title)
    if subtitle:
        st.markdown(f"*{subtitle}*")
    st.divider()


def render_sidebar() -> None:
    """Render application sidebar with navigation."""
    with st.sidebar:
        st.header("Navigation")
        st.info("Use the tabs above to navigate between features")


def render_footer() -> None:
    """Render application footer."""
    from app.config.settings import settings as app_settings
    st.divider()
    st.markdown(
        f"""
        <div style='text-align: center; color: gray; padding: 1rem;'>
            <small>{app_settings.APP_NAME} v{app_settings.APP_VERSION}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_success(message: str) -> None:
    """Display success message."""
    st.success(f"✅ {message}")


def show_error(message: str) -> None:
    """Display error message."""
    st.error(f"❌ {message}")


def show_warning(message: str) -> None:
    """Display warning message."""
    st.warning(f"⚠️ {message}")


def show_info(message: str) -> None:
    """Display info message."""
    st.info(f"ℹ️ {message}")


# ============================================================================
# AGENT OS FLASH LABELS (Phase 2A)
# ============================================================================


def render_compact_flash_labels() -> None:
    """
    Render a compact Flash Labels bar for visibility during chat.

    This shows the current Agent OS section completion status
    in a non-intrusive bar format.
    """
    from app.services.agent_os_service import (
        AgentOSDocument,
        create_empty_template,
    )

    # Get document from session state
    doc = None
    if "agent_os_doc" in st.session_state:
        doc = st.session_state.agent_os_doc
    else:
        return  # No document yet, nothing to show

    # Get section statuses
    statuses = doc.get_section_status()

    # Count statuses
    empty_count = sum(1 for s in statuses.values() if s == "empty")
    partial_count = sum(1 for s in statuses.values() if s == "partial")
    complete_count = sum(1 for s in statuses.values() if s == "complete")
    total = len(statuses)

    # Calculate completion percentage
    percentage = doc.calculate_completion()

    # Determine overall color
    if percentage < 50:
        bar_color = "#ef4444"
        bg_color = "#fef2f2"
    elif percentage < 80:
        bar_color = "#f59e0b"
        bg_color = "#fffbeb"
    else:
        bar_color = "#10b981"
        bg_color = "#d1fae5"

    # Build compact flash labels bar
    st.markdown(f"""
    <div style="
        background: {bg_color};
        border: 1px solid {bar_color};
        border-radius: 8px;
        padding: 8px 12px;
        margin: 8px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
    ">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-weight: 600; color: {bar_color};">Agent OS: {percentage}%</span>
            <span style="font-size: 12px; color: #666;">
                {complete_count}/{total} sections complete
            </span>
        </div>
        <div style="display: flex; gap: 6px; flex-wrap: wrap;">
            <span style="
                background: #26de81;
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 11px;
            ">[x] {complete_count}</span>
            <span style="
                background: #ffa502;
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 11px;
            ">[~] {partial_count}</span>
            <span style="
                background: #ff6b6b;
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 11px;
            ">[ ] {empty_count}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_mini_gap_indicator() -> None:
    """
    Render a minimal gap indicator for non-intrusive display.

    Shows just the percentage and gap count in a small badge.
    """
    from app.services.agent_os_service import AgentOSDocument

    doc = st.session_state.get("agent_os_doc")
    if not doc:
        return

    percentage = doc.calculate_completion()
    gap_summary = doc.get_gap_summary()

    # Determine color
    if percentage < 50:
        color = "#dc2626"
    elif percentage < 80:
        color = "#d97706"
    else:
        color = "#059669"

    # Just show a small indicator
    if gap_summary['total_gaps'] > 0:
        st.markdown(f"""
        <div style="
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 12px;
        ">
            <span style="color: {color}; font-weight: 600;">{percentage}%</span>
            <span style="color: #666;">|</span>
            <span style="color: #888;">{gap_summary['total_gaps']} gaps</span>
        </div>
        """, unsafe_allow_html=True)


# ============================================================================
# VOICE INPUT STATUS INDICATORS (Phase 2B)
# ============================================================================


def render_voice_recording_indicator() -> None:
    """
    Render a voice recording status indicator.

    Shows when voice recording is active (for Click-to-Rant or Real-Time Tagging).
    Displays in a non-intrusive way during chat sessions.
    """
    # Check for Click-to-Rant recording
    target_section = st.session_state.get("voice_target_section")
    if target_section:
        st.markdown(f"""
        <div style="
            background: linear-gradient(90deg, #0ea5e9, #0284c7);
            color: white;
            padding: 8px 16px;
            border-radius: 8px;
            margin: 8px 0;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
        ">
            <span style="animation: pulse 1s infinite;">MIC</span>
            <span>Recording to: <strong>{target_section}</strong></span>
            <span style="margin-left: auto; font-size: 12px; opacity: 0.8;">Click-to-Rant mode</span>
        </div>
        <style>
            @keyframes pulse {{
                0% {{ opacity: 1; }}
                50% {{ opacity: 0.5; }}
                100% {{ opacity: 1; }}
            }}
        </style>
        """, unsafe_allow_html=True)
        return

    # Check for Real-Time Tagging recording
    is_realtime_recording = st.session_state.get("realtime_recording_active", False)
    if is_realtime_recording:
        import time
        start_time = st.session_state.get("realtime_recording_start", 0)
        elapsed = time.time() - start_time if start_time else 0
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        elapsed_str = f"{minutes:02d}:{seconds:02d}"

        current_tag = st.session_state.get("realtime_current_tag", "None")
        tag_count = len(st.session_state.get("realtime_tag_events", []))

        st.markdown(f"""
        <div style="
            background: linear-gradient(90deg, #dc2626, #ef4444);
            color: white;
            padding: 8px 16px;
            border-radius: 8px;
            margin: 8px 0;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
        ">
            <span style="animation: pulse 1s infinite; font-weight: bold;">REC {elapsed_str}</span>
            <span>|</span>
            <span>Tag: <strong>{current_tag}</strong></span>
            <span>|</span>
            <span>{tag_count} tags</span>
            <span style="margin-left: auto; font-size: 12px; opacity: 0.8;">Real-Time Tagging mode</span>
        </div>
        <style>
            @keyframes pulse {{
                0% {{ opacity: 1; }}
                50% {{ opacity: 0.5; }}
                100% {{ opacity: 1; }}
            }}
        </style>
        """, unsafe_allow_html=True)


def render_voice_mode_selector(compact: bool = True) -> Optional[str]:
    """
    Render a compact voice mode selector.

    Can be shown in the chat panel for quick voice input access.

    Args:
        compact: If True, show a minimal selector

    Returns:
        Selected mode if changed, None otherwise
    """
    if compact:
        cols = st.columns([1, 1, 2])
        with cols[0]:
            ctr_btn = st.button("Click-to-Rant", key="quick_ctr", use_container_width=True)
        with cols[1]:
            rtt_btn = st.button("Real-Time Tag", key="quick_rtt", use_container_width=True)

        if ctr_btn:
            return "click_to_rant"
        if rtt_btn:
            return "real_time_tag"

    return None


def is_voice_recording_active() -> bool:
    """
    Check if any voice recording mode is currently active.

    Returns:
        True if recording is active
    """
    # Check Click-to-Rant
    if st.session_state.get("voice_target_section"):
        return True

    # Check Real-Time Tagging
    if st.session_state.get("realtime_recording_active"):
        return True

    return False


def clear_voice_recording_state() -> None:
    """
    Clear all voice recording state.

    Used when canceling or completing a recording.
    """
    keys_to_clear = [
        "voice_target_section",
        "voice_input_mode",
        "voice_recording_active",
        "realtime_recording_active",
        "realtime_recording_start",
        "realtime_tag_events",
        "realtime_current_tag",
    ]

    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


# Project Selection Components

def render_user_selector(db: Session, users: List[UserProfile]) -> Optional[UserProfile]:
    """
    Render user selection dropdown.

    Args:
        db: Database session
        users: List of users

    Returns:
        Selected user or None
    """
    if not users:
        show_warning("No users found. Please create a user first.")
        return None

    user_options = {f"{user.username} ({user.email})": user for user in users}
    user_names = list(user_options.keys())

    # Initialize session state
    if "selected_user_name" not in st.session_state:
        st.session_state.selected_user_name = user_names[0]

    selected_name = st.selectbox(
        "Select User",
        user_names,
        key="user_selector",
        index=user_names.index(st.session_state.selected_user_name) if st.session_state.selected_user_name in user_names else 0
    )

    st.session_state.selected_user_name = selected_name
    return user_options[selected_name]


def render_project_selector(
    db: Session,
    user: UserProfile
) -> Tuple[Optional[Project], bool]:
    """
    Render project selection dropdown with create new option.

    Args:
        db: Database session
        user: Current user

    Returns:
        Tuple of (selected_project, should_create_new)
    """
    projects = list_user_projects(db, user.id)

    if not projects:
        st.info("📁 No projects yet – create your first project below!")
        if st.button("➕ Create First Project", type="primary", use_container_width=True):
            return None, True
        return None, False

    # Build project options
    project_options = {p.name: p for p in projects}
    project_names = list(project_options.keys())

    # Determine current selection
    current_selection = None

    # First priority: use current_project_id if set
    if "current_project_id" in st.session_state:
        for name, proj in project_options.items():
            if proj.id == st.session_state.current_project_id:
                current_selection = name
                break

    # Second priority: use selected_project_name if set and valid
    if not current_selection and "selected_project_name" in st.session_state:
        if st.session_state.selected_project_name in project_names:
            current_selection = st.session_state.selected_project_name

    # Default: select first project
    if not current_selection:
        current_selection = project_names[0]

    # Update session state to match
    st.session_state.selected_project_name = current_selection

    # Render selectbox
    col1, col2 = st.columns([3, 1])

    with col1:
        selected_name = st.selectbox(
            "Select Project",
            project_names,
            index=project_names.index(current_selection),
            key="project_selector",
        )

        # Update session state when selection changes
        if selected_name != st.session_state.selected_project_name:
            st.session_state.selected_project_name = selected_name
            selected_project = project_options[selected_name]
            st.session_state.current_project_id = selected_project.id
            st.session_state.current_project_name = selected_project.name
            st.rerun()

    with col2:
        if st.button("➕ New", help="Create a new project", use_container_width=True):
            return None, True

    # Return the selected project
    selected_project = project_options[selected_name]
    return selected_project, False


def render_create_project_form(db: Session, user: UserProfile) -> Optional[Project]:
    """
    Render form to create a new project.

    Args:
        db: Database session
        user: Current user

    Returns:
        Created project or None
    """
    st.subheader("Create New Project")

    with st.form("create_project_form"):
        name = st.text_input("Project Name *", placeholder="My Design Project")
        description = st.text_area(
            "Description (optional)",
            placeholder="Describe your project...",
            height=100
        )

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("Create Project", type="primary")
        with col2:
            cancel = st.form_submit_button("Cancel")

        if submit:
            if not name or not name.strip():
                show_error("Project name is required")
                return None

            try:
                project = create_project(
                    db,
                    name=name.strip(),
                    owner_id=user.id,
                    description=description.strip() if description else None
                )
                show_success(f"Project '{project.name}' created successfully!")
                st.session_state.selected_project_name = project.name
                st.rerun()
            except Exception as e:
                show_error(f"Failed to create project: {str(e)}")
                return None

        if cancel:
            st.rerun()

    return None


# Settings UI Components

def render_settings_ui(db: Session, user_id: Optional[int] = None) -> None:
    """
    Render settings UI with all configuration options.

    Args:
        db: Database session
        user_id: User ID for user-specific settings (None for global)
    """
    st.subheader("⚙️ Settings")
    st.markdown("Configure application and AI model settings.")

    # Load current settings
    current_settings = get_all_settings(db, user_id)

    with st.form("settings_form"):
        st.markdown("### API Configuration")

        openai_key = st.text_input(
            "OpenAI API Key (optional, uses env if blank)",
            value=current_settings.get("OPENAI_API_KEY", ""),
            type="password",
            help="Leave blank to use OPENAI_API_KEY from environment"
        )

        anthropic_key = st.text_input(
            "Anthropic API Key (for Claude models)",
            value=current_settings.get("ANTHROPIC_API_KEY", ""),
            type="password",
            help="Required for Roundtable Coder with Claude models"
        )

        google_key = st.text_input(
            "Google API Key (for Gemini models)",
            value=current_settings.get("GOOGLE_API_KEY", ""),
            type="password",
            help="Required for Roundtable Coder with Gemini models"
        )

        col1, col2 = st.columns(2)
        with col1:
            chat_model = st.text_input(
                "Default Chat Model",
                value=current_settings.get("DEFAULT_CHAT_MODEL", "gpt-4-turbo-preview"),
                help="OpenAI model for chat interactions"
            )

        with col2:
            summary_model = st.text_input(
                "Default Summary Model",
                value=current_settings.get("DEFAULT_SUMMARY_MODEL", "gpt-4-turbo-preview"),
                help="OpenAI model for generating summaries"
            )

        st.markdown("### Context & Baton Settings")

        col1, col2 = st.columns(2)
        with col1:
            max_tokens = st.number_input(
                "Max Context Tokens",
                value=int(current_settings.get("max_context_tokens", "8000")),
                min_value=1000,
                max_value=128000,
                step=1000,
                help="Maximum tokens for context"
            )

        with col2:
            baton_threshold = st.number_input(
                "Auto Baton Threshold (%)",
                value=int(current_settings.get("auto_baton_threshold_percent", "80")),
                min_value=0,
                max_value=100,
                step=5,
                help="Trigger baton creation at this percentage of max tokens"
            )

        auto_warmup = st.checkbox(
            "Enable Auto Warmup",
            value=current_settings.get("auto_warmup_enabled", "true").lower() == "true",
            help="Automatically warm up AI with project context"
        )

        st.markdown("### Warmup Prompts")
        st.caption("These prompts are used to warm up the AI with project context.")

        warmup_1 = st.text_area(
            "Warmup Prompt 1",
            value=current_settings.get("warmup_prompt_1", ""),
            height=80
        )

        warmup_2 = st.text_area(
            "Warmup Prompt 2",
            value=current_settings.get("warmup_prompt_2", ""),
            height=80
        )

        warmup_3 = st.text_area(
            "Warmup Prompt 3",
            value=current_settings.get("warmup_prompt_3", ""),
            height=80
        )

        warmup_4 = st.text_area(
            "Warmup Prompt 4",
            value=current_settings.get("warmup_prompt_4", ""),
            height=80
        )

        st.markdown("### Baton Description Prompt")
        st.caption("Template for generating baton descriptions.")

        baton_prompt = st.text_area(
            "Baton Description Prompt",
            value=current_settings.get("baton_description_prompt", ""),
            height=100,
            help="Prompt template for AI to generate baton descriptions"
        )

        st.markdown("### Security")

        pin_code = st.text_input(
            "PIN Code (optional)",
            value=current_settings.get("pin_code", ""),
            type="password",
            help="Optional PIN for additional security"
        )

        st.divider()

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            save_button = st.form_submit_button("💾 Save Settings", type="primary")
        with col2:
            reset_button = st.form_submit_button("🔄 Reset to Defaults")

        if save_button:
            try:
                new_settings = {
                    "OPENAI_API_KEY": openai_key,
                    "ANTHROPIC_API_KEY": anthropic_key,
                    "GOOGLE_API_KEY": google_key,
                    "DEFAULT_CHAT_MODEL": chat_model,
                    "DEFAULT_SUMMARY_MODEL": summary_model,
                    "max_context_tokens": str(max_tokens),
                    "auto_baton_threshold_percent": str(baton_threshold),
                    "auto_warmup_enabled": "true" if auto_warmup else "false",
                    "warmup_prompt_1": warmup_1,
                    "warmup_prompt_2": warmup_2,
                    "warmup_prompt_3": warmup_3,
                    "warmup_prompt_4": warmup_4,
                    "baton_description_prompt": baton_prompt,
                    "pin_code": pin_code,
                }

                set_multiple_settings(db, new_settings, user_id)
                show_success("Settings saved successfully!")
                st.rerun()
            except Exception as e:
                show_error(f"Failed to save settings: {str(e)}")

        if reset_button:
            try:
                from app.services.settings_service import DEFAULT_SETTINGS
                set_multiple_settings(db, DEFAULT_SETTINGS, user_id)
                show_success("Settings reset to defaults!")
                st.rerun()
            except Exception as e:
                show_error(f"Failed to reset settings: {str(e)}")


# Project Context UI Components

def render_project_context_ui(db: Session, project: Project) -> None:
    """
    Render project context UI.

    Args:
        db: Database session
        project: Current project
    """
    st.subheader("📋 Project Context")
    st.markdown(f"Manage context and guidelines for **{project.name}**")

    # Get current context
    context = get_project_context(db, project.id)

    # Description Mode Selector
    st.markdown("#### Description Mode")
    current_mode = context.description_mode if context else DescriptionMode.MANUAL

    mode_options = {
        "Manual Only": DescriptionMode.MANUAL,
        "Auto-Generated Only": DescriptionMode.AUTO,
        "Merged (Manual + Auto)": DescriptionMode.MERGE
    }

    selected_mode_label = [k for k, v in mode_options.items() if v == current_mode][0]

    new_mode_label = st.selectbox(
        "Choose how to combine manual and auto descriptions",
        options=list(mode_options.keys()),
        index=list(mode_options.keys()).index(selected_mode_label),
        help="Manual: use only manual description | Auto: use only AI-generated | Merge: combine both"
    )

    new_mode = mode_options[new_mode_label]

    # Update mode if changed
    if new_mode != current_mode:
        try:
            update_description_mode(db, project.id, new_mode)
            show_success(f"Description mode updated to: {new_mode_label}")
            st.rerun()
        except Exception as e:
            show_error(f"Failed to update mode: {str(e)}")

    st.divider()

    # Manual description
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Manual Description")
        st.caption("Describe your project, design system, and guidelines.")

    with col2:
        if st.button("💾 Save Manual", help="Save manual description"):
            st.session_state.save_context_clicked = True

    # Manual description editor
    manual_desc = st.text_area(
        "Manual Description",
        value=context.content if context else "",
        height=250,
        label_visibility="collapsed",
        help="Enter project context, design guidelines, constraints, etc."
    )

    # Save context if button was clicked
    if st.session_state.get("save_context_clicked"):
        try:
            update_project_context(db, project.id, manual_desc)
            show_success("Manual description saved successfully!")
            st.session_state.save_context_clicked = False
            st.rerun()
        except Exception as e:
            show_error(f"Failed to save description: {str(e)}")

    st.divider()

    # Auto description
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Auto Description")
        st.caption("AI-generated summary from your project nodes and structure.")

    with col2:
        regenerate_btn = st.button("🔄 Regenerate", help="Generate fresh auto-description from current project state")

    # Regenerate auto description if button clicked
    if regenerate_btn:
        with st.spinner("Generating auto-description from project nodes..."):
            try:
                settings = get_all_settings(db)
                auto_desc = generate_auto_project_description(db, project.id, settings)
                show_success("Auto-description generated successfully!")
                st.rerun()
            except Exception as e:
                show_error(f"Failed to generate auto-description: {str(e)}")

    # Display auto-generated content
    auto_desc_value = context.auto_description if context and context.auto_description else "(No auto-description generated yet. Click 'Regenerate' above.)"

    st.text_area(
        "Auto-generated description",
        value=auto_desc_value,
        height=250,
        disabled=True,
        label_visibility="collapsed",
        help="This description is automatically generated from your project structure and nodes"
    )

    st.divider()

    # Preview of combined description based on mode
    with st.expander("👁️ Preview Combined Description", expanded=False):
        st.markdown("**This is how the description will appear in Batons and Truth Doc:**")
        st.divider()
        combined = get_combined_description(db, project.id)
        st.markdown(combined)


def render_truth_doc_export_ui(db: Session, project: Project) -> None:
    """
    Render Truth Doc export UI.

    Args:
        db: Database session
        project: Current project
    """
    st.subheader("📄 Truth Doc Export")
    st.markdown(f"Export comprehensive documentation for **{project.name}**")

    st.info(
        "Truth Doc is a complete markdown document containing your project description, "
        "all components with their versions, and full history. Perfect for documentation, "
        "handoffs, or archival."
    )

    # Export options
    include_archived = st.checkbox(
        "Include archived/deleted nodes",
        value=False,
        help="Include components that have been archived or deleted"
    )

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        preview_btn = st.button("👁️ Preview", type="secondary", use_container_width=True)

    with col2:
        export_btn = st.button("📥 Export", type="primary", use_container_width=True)

    # Preview Truth Doc
    if preview_btn:
        with st.spinner("Generating Truth Doc preview..."):
            try:
                truth_doc = export_truth_doc(db, project.id, include_archived)
                preview = get_truth_doc_preview(truth_doc, max_lines=100)

                st.divider()
                st.markdown("### Truth Doc Preview")
                st.caption(f"Showing first 100 lines. Full document has {len(truth_doc.split(chr(10)))} lines.")

                st.code(preview, language="markdown")

                # Store full doc in session for download
                st.session_state.truth_doc_full = truth_doc
                st.session_state.truth_doc_filename = get_truth_doc_filename(project.name)

            except Exception as e:
                show_error(f"Failed to generate preview: {str(e)}")

    # Export Truth Doc
    if export_btn:
        with st.spinner("Generating complete Truth Doc..."):
            try:
                truth_doc = export_truth_doc(db, project.id, include_archived)
                filename = get_truth_doc_filename(project.name)

                # Store in session
                st.session_state.truth_doc_full = truth_doc
                st.session_state.truth_doc_filename = filename

                show_success(f"Truth Doc generated! ({len(truth_doc)} characters, {len(truth_doc.split(chr(10)))} lines)")

                st.divider()

                # Download button
                st.download_button(
                    label="💾 Download Truth Doc",
                    data=truth_doc,
                    file_name=filename,
                    mime="text/markdown",
                    type="primary",
                    use_container_width=True
                )

                # Copy to clipboard option
                st.markdown("**Or copy to clipboard:**")
                st.code(truth_doc, language="markdown", line_numbers=False)

            except Exception as e:
                show_error(f"Failed to generate Truth Doc: {str(e)}")

    # If doc is in session, show download button
    if st.session_state.get("truth_doc_full"):
        st.divider()
        st.markdown("### Download Truth Doc")

        st.download_button(
            label="💾 Download Truth Doc",
            data=st.session_state.truth_doc_full,
            file_name=st.session_state.get("truth_doc_filename", "truth_doc.md"),
            mime="text/markdown",
            use_container_width=True
        )


# Chat Panel Components

def render_token_meter(
    db: Session,
    session_id: int,
    max_tokens: int = 8000
) -> None:
    """
    Render token usage meter with color-coded progress bar.

    Args:
        db: Database session
        session_id: Chat session ID
        max_tokens: Maximum context tokens
    """
    # Get token usage
    token_usage = get_token_usage(db, session_id)
    total_tokens = token_usage["total_tokens_used"]

    # Calculate percentage
    percent_used = (total_tokens / max_tokens) * 100 if max_tokens > 0 else 0
    percent_used = min(percent_used, 100)  # Cap at 100%

    # Determine color based on usage
    if percent_used < 50:
        color = "🟢"  # Green
        bar_color = "normal"
    elif percent_used < 70:
        color = "🟡"  # Yellow
        bar_color = "normal"
    elif percent_used < 90:
        color = "🟠"  # Orange
        bar_color = "normal"
    else:
        color = "🔴"  # Red
        bar_color = "normal"

    # Display meter
    st.markdown(f"**{color} Token Usage: {total_tokens:,} / {max_tokens:,}** ({percent_used:.1f}%)")

    # Progress bar
    st.progress(percent_used / 100)

    # Token breakdown in expander
    with st.expander("Token Details"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Prompt Tokens", f"{token_usage['total_prompt_tokens']:,}")
        with col2:
            st.metric("Completion Tokens", f"{token_usage['total_completion_tokens']:,}")
        with col3:
            st.metric("Total Used", f"{total_tokens:,}")


def render_chat_panel(
    db: Session,
    user_id: int,
    project: Project
) -> None:
    """
    Render chat panel with message history and input.

    Args:
        db: Database session
        user_id: Current user ID
        project: Current project
    """
    st.subheader("💬 AI Chat")

    # Check for warmed pending sessions
    warmed_sessions = get_warmed_sessions(db, user_id, project.id)
    if warmed_sessions and "baton_notification_shown" not in st.session_state:
        st.success(f"🎯 New warmed session ready! ({len(warmed_sessions)} available)")
        st.session_state.baton_notification_shown = True

    # Get or create chat session
    # Check if we should use a different session from session state
    if "current_chat_session_id" in st.session_state:
        from app.core.models import ChatSession
        chat_session = db.query(ChatSession).filter(
            ChatSession.id == st.session_state.current_chat_session_id,
            ChatSession.user_id == user_id,
            ChatSession.project_id == project.id
        ).first()
        if not chat_session:
            # Session not found, get default
            chat_session = get_or_create_chat_session(db, user_id, project.id)
            st.session_state.current_chat_session_id = chat_session.id
    else:
        chat_session = get_or_create_chat_session(db, user_id, project.id)
        st.session_state.current_chat_session_id = chat_session.id

    # Display current project and session info (Phase 8)
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.markdown(f"**Project:** {project.name}")
    with col2:
        st.markdown(f"**Session:** {chat_session.title}")
    with col3:
        # New session button
        new_session_clicked = st.button("🆕 New", help="Start a new clean session (no baton)", use_container_width=True)

    # =========================================================================
    # AGENT OS FLASH LABELS - Visible during chat (Phase 2A)
    # =========================================================================
    # Show compact flash labels if Agent OS doc exists
    if "agent_os_doc" in st.session_state:
        render_compact_flash_labels()

    # =========================================================================
    # VOICE RECORDING INDICATOR (Phase 2B)
    # =========================================================================
    # Show voice recording status if active
    if is_voice_recording_active():
        render_voice_recording_indicator()

    if new_session_clicked:
        try:
            from datetime import datetime
            from app.core.models import ChatSession, SessionStatus

            # Create new clean session
            new_session = ChatSession(
                user_id=user_id,
                project_id=project.id,
                title=f"Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                description="Clean session without baton",
                session_type="general",
                is_active=True,
                status=SessionStatus.ACTIVE,
                total_prompt_tokens=0,
                total_completion_tokens=0,
                total_tokens_used=0
            )
            db.add(new_session)

            # Deactivate old session
            chat_session.is_active = False

            db.commit()
            db.refresh(new_session)

            # Update session state
            st.session_state.current_chat_session_id = new_session.id
            show_success("New clean session started!")
            st.rerun()
        except Exception as e:
            show_error(f"Failed to create new session: {str(e)}")

    st.divider()

    # Session switcher
    if warmed_sessions:
        with st.expander("🔄 Switch to Warmed Session", expanded=False):
            for warmed in warmed_sessions:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{warmed.title}**")
                    st.caption(f"Created: {warmed.created_at.strftime('%Y-%m-%d %H:%M')}")
                with col2:
                    if st.button("Switch", key=f"switch_{warmed.id}"):
                        switch_to_session(db, chat_session.id, warmed.id)
                        st.session_state.current_chat_session_id = warmed.id
                        st.session_state.baton_notification_shown = False
                        show_success("Switched to warmed session!")
                        st.rerun()

    # Get settings
    settings = get_all_settings(db)
    max_tokens = int(settings.get("max_context_tokens", "8000"))
    chat_model = settings.get("DEFAULT_CHAT_MODEL", "gpt-4-turbo-preview")
    openai_key = settings.get("OPENAI_API_KEY", "")

    # Token meter
    render_token_meter(db, chat_session.id, max_tokens)

    st.divider()

    # Chat history with warm-up toggle
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("#### Conversation")
    with col2:
        show_warmup = st.checkbox("Show warm-up", value=False, key="show_warmup_toggle")

    messages = get_chat_history(db, chat_session.id)

    # Display messages in a container with scrolling
    chat_container = st.container()

    with chat_container:
        if not messages:
            st.info("Start a conversation by typing a message below.")
        else:
            for msg in messages:
                # Filter warm-up messages based on toggle
                if msg.is_warmup and not show_warmup:
                    continue

                # Skip system messages unless showing warmup
                if msg.role.value == "system":
                    if show_warmup:
                        with st.chat_message("assistant", avatar="📋"):
                            st.markdown(f"*System: {msg.content[:200]}...*" if len(msg.content) > 200 else f"*System: {msg.content}*")
                    continue

                # Add warm-up indicator
                warmup_indicator = " 🔥" if msg.is_warmup else ""

                if msg.role.value == "user":
                    with st.chat_message("user"):
                        st.markdown(msg.content + warmup_indicator)
                elif msg.role.value == "assistant":
                    with st.chat_message("assistant"):
                        st.markdown(msg.content + warmup_indicator)

    st.divider()

    # Input area - use text_area for larger input
    user_input = st.text_area(
        "Message",
        key="chat_input",
        placeholder="Type your message...",
        label_visibility="collapsed",
        height=100
    )

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        send_button = st.button("📤 Send", type="primary", use_container_width=True)

    with col2:
        if st.button("🗑️ Clear", help="Clear chat history"):
            clear_chat_history(db, chat_session.id)
            st.rerun()

    with col3:
        baton_button = st.button("🎯 Baton Now", help="Create a new warmed session with project snapshot")

    # Manual baton creation
    if baton_button:
        with st.spinner("Creating baton snapshot and warming new session..."):
            try:
                baton, new_session = generate_baton(
                    db=db,
                    user_id=user_id,
                    project_id=project.id,
                    from_session_id=chat_session.id,
                    settings=settings,
                    run_warmup=True
                )
                show_success(f"Baton created! New warmed session: {new_session.title}")
                st.session_state.baton_notification_shown = False
                st.rerun()
            except Exception as e:
                show_error(f"Failed to create baton: {str(e)}")

    # Send message
    if send_button and user_input and user_input.strip():
        with st.spinner("Thinking..."):
            try:
                user_msg, assistant_msg = send_chat_message(
                    db,
                    project.id,
                    chat_session.id,
                    user_input.strip(),
                    openai_api_key=openai_key if openai_key else None,
                    chat_model=chat_model
                )

                # Auto-detect potential nodes from this exchange
                if openai_key or settings.get("OPENAI_API_KEY"):
                    api_key_for_detection = openai_key or settings.get("OPENAI_API_KEY")
                    detected = detect_nodes_from_exchange(
                        user_message=user_input.strip(),
                        assistant_message=assistant_msg.content,
                        openai_api_key=api_key_for_detection,
                        model=settings.get("DEFAULT_SUMMARY_MODEL", "gpt-4-turbo-preview")
                    )
                    if detected:
                        # Store detected nodes in session state for UI display
                        st.session_state.detected_nodes = detected
                        st.session_state.detected_nodes_project_id = project.id

                # Check for auto-baton trigger
                if check_auto_baton_trigger(db, chat_session.id, settings):
                    show_info("Token threshold reached! Creating auto-baton...")
                    try:
                        auto_baton, auto_session = generate_baton(
                            db=db,
                            user_id=user_id,
                            project_id=project.id,
                            from_session_id=chat_session.id,
                            settings=settings,
                            run_warmup=True
                        )
                        # Update baton type to auto
                        auto_baton.snapshot_type = "auto"
                        db.commit()

                        st.session_state.baton_notification_shown = False
                        show_success("Auto-baton created! A new warmed session is ready.")
                    except Exception as e:
                        show_warning(f"Auto-baton creation failed: {str(e)}")

                st.rerun()
            except Exception as e:
                show_error(f"Chat error: {str(e)}")
    elif send_button and not user_input.strip():
        show_warning("Please enter a message")

    # Display detected node suggestions
    _render_detected_nodes_ui(db, project.id)


def _render_detected_nodes_ui(db: Session, project_id: int) -> None:
    """
    Render UI for detected node suggestions.

    Shows a popup/expander when potential nodes are detected from chat.
    Allows user to accept, edit, or dismiss detected nodes.

    Args:
        db: Database session
        project_id: Current project ID
    """
    # Check if we have detected nodes for current project
    if "detected_nodes" not in st.session_state:
        return

    if st.session_state.get("detected_nodes_project_id") != project_id:
        return

    detected_nodes = st.session_state.detected_nodes
    if not detected_nodes:
        return

    # Show detected nodes in an expander (auto-expanded)
    with st.expander("🔍 **Potential Nodes Detected!**", expanded=True):
        st.markdown("The AI detected items that might be worth tracking as nodes:")

        for idx, node in enumerate(detected_nodes):
            icon = get_node_type_icon(node.suggested_type)
            confidence_pct = int(node.confidence * 100)

            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.markdown(f"**{icon} {node.suggested_name}** ({node.suggested_type.value})")
                st.caption(f"{node.suggested_description}")
                st.caption(f"Confidence: {confidence_pct}% | *{node.reason}*")

            with col2:
                # Create node button
                if st.button("✅ Create", key=f"create_node_{idx}", help="Create this node"):
                    try:
                        new_node = create_node(
                            db=db,
                            project_id=project_id,
                            name=node.suggested_name,
                            node_type=node.suggested_type,
                            description=node.suggested_description,
                            status=NodeStatus.DRAFT
                        )
                        show_success(f"Created node: {node.suggested_name}")
                        # Remove this node from the list
                        st.session_state.detected_nodes = [
                            n for i, n in enumerate(detected_nodes) if i != idx
                        ]
                        st.rerun()
                    except Exception as e:
                        show_error(f"Failed to create node: {str(e)}")

            with col3:
                # Dismiss button
                if st.button("❌ Skip", key=f"dismiss_node_{idx}", help="Dismiss this suggestion"):
                    # Remove this node from the list
                    st.session_state.detected_nodes = [
                        n for i, n in enumerate(detected_nodes) if i != idx
                    ]
                    st.rerun()

            st.divider()

        # Dismiss all button
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("✅ Create All", help="Create all suggested nodes"):
                created_count = 0
                for node in detected_nodes:
                    try:
                        create_node(
                            db=db,
                            project_id=project_id,
                            name=node.suggested_name,
                            node_type=node.suggested_type,
                            description=node.suggested_description,
                            status=NodeStatus.DRAFT
                        )
                        created_count += 1
                    except Exception as e:
                        show_warning(f"Could not create '{node.suggested_name}': {str(e)}")
                if created_count > 0:
                    show_success(f"Created {created_count} nodes!")
                st.session_state.detected_nodes = []
                st.rerun()

        with col2:
            if st.button("❌ Dismiss All", help="Dismiss all suggestions"):
                st.session_state.detected_nodes = []
                st.rerun()


# ============================================================================
# COCKPIT DASHBOARD MODE (Phase 4 - Mechanism 4)
# ============================================================================


def render_cockpit_mode_toggle() -> bool:
    """
    Render toggle for Cockpit Mode.

    Returns:
        True if cockpit mode is active
    """
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("**Layout Mode**")

    with col2:
        cockpit_mode = st.toggle(
            "Cockpit",
            value=st.session_state.get("cockpit_mode_active", False),
            key="cockpit_mode_toggle",
            help="Enable cockpit mode for all-panels-visible dashboard"
        )

    if cockpit_mode != st.session_state.get("cockpit_mode_active", False):
        st.session_state.cockpit_mode_active = cockpit_mode
        st.rerun()

    return cockpit_mode


def render_cockpit_dashboard(
    db: Session,
    project: "Project",
    session_id: Optional[int] = None
) -> Optional[str]:
    """
    Render the Cockpit Dashboard - all features visible in a grid.

    Like an airplane cockpit - many small panels, all visible at once.
    Tap any to expand.

    Args:
        db: Database session
        project: Current project
        session_id: Optional chat session ID

    Returns:
        Name of panel that was clicked to expand, if any
    """
    from app.services.agent_os_service import AgentOSDocument, create_empty_template

    st.markdown("## Cockpit Dashboard")
    st.caption("All features at a glance. Click any panel to expand.")

    # Get Agent OS document
    doc = st.session_state.get("agent_os_doc")
    if not doc:
        doc = create_empty_template(project.name)
        st.session_state.agent_os_doc = doc

    clicked_panel = None

    # Panel definitions
    panels = [
        ("chat", "Chat", "Message exchange with AI"),
        ("tree", "Tree View", "Hierarchical Agent OS view"),
        ("gaps", "Gap Analysis", "Missing sections analysis"),
        ("voice", "Voice Input", "Click-to-Rant & Real-Time Tagging"),
        ("spec", "Spec View", "Full specification document"),
        ("tags", "Tag Overlay", "Raw rant with tags"),
        ("panels", "Multi-Panel", "All sections at once"),
        ("config", "Settings", "Configuration & Lab Mode"),
    ]

    # Create 2 rows of 4 panels
    row1_panels = panels[:4]
    row2_panels = panels[4:]

    # Row 1
    cols1 = st.columns(4)
    for idx, (key, label, description) in enumerate(row1_panels):
        with cols1[idx]:
            if _render_cockpit_panel(key, label, description, doc):
                clicked_panel = key

    # Row 2
    cols2 = st.columns(4)
    for idx, (key, label, description) in enumerate(row2_panels):
        with cols2[idx]:
            if _render_cockpit_panel(key, label, description, doc):
                clicked_panel = key

    # Handle panel expansion
    if clicked_panel:
        st.session_state.expanded_cockpit_panel = clicked_panel

    # Render expanded panel if any
    expanded = st.session_state.get("expanded_cockpit_panel")
    if expanded:
        st.divider()
        _render_expanded_cockpit_panel(expanded, db, project, doc, session_id)

    return clicked_panel


def _render_cockpit_panel(
    key: str,
    label: str,
    description: str,
    doc: "AgentOSDocument"
) -> bool:
    """
    Render a single cockpit panel.

    Args:
        key: Panel key
        label: Panel label
        description: Panel description
        doc: AgentOSDocument for status

    Returns:
        True if panel was clicked
    """
    # Get panel-specific status/preview
    status_icon, preview = _get_cockpit_panel_status(key, doc)

    # Check if this panel is currently expanded
    is_expanded = st.session_state.get("expanded_cockpit_panel") == key

    # Panel styling
    border_color = "#3b82f6" if is_expanded else "#374151"
    bg_color = "#1e3a5f" if is_expanded else "#1f2937"

    panel_html = f'''
    <div style="
        background: {bg_color};
        border: 2px solid {border_color};
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        min-height: 100px;
    ">
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        ">
            <span style="
                font-size: 14px;
                font-weight: 600;
                color: #e5e7eb;
            ">{status_icon} {label}</span>
        </div>
        <div style="
            font-size: 11px;
            color: #9ca3af;
            margin-bottom: 8px;
        ">{description}</div>
        <div style="
            font-size: 12px;
            color: #6b7280;
        ">{preview}</div>
    </div>
    '''

    st.markdown(panel_html, unsafe_allow_html=True)

    # Button for clicking
    btn_label = "Collapse" if is_expanded else "Expand"
    return st.button(
        btn_label,
        key=f"cockpit_panel_{key}",
        use_container_width=True,
        type="primary" if is_expanded else "secondary"
    )


def _get_cockpit_panel_status(key: str, doc: "AgentOSDocument") -> tuple:
    """
    Get status icon and preview for a cockpit panel.

    Args:
        key: Panel key
        doc: AgentOSDocument

    Returns:
        Tuple of (status_icon, preview_text)
    """
    if key == "chat":
        return ("Messages", "Send messages to AI")

    elif key == "tree":
        completion = doc.completion_percentage
        return (f"{completion}%", f"Document completion: {completion}%")

    elif key == "gaps":
        gap_summary = doc.get_gap_summary()
        return (
            f"{gap_summary['total_gaps']} gaps",
            f"{gap_summary['critical_count']} critical, {gap_summary['minor_count']} minor"
        )

    elif key == "voice":
        is_recording = st.session_state.get("realtime_recording_active", False)
        target = st.session_state.get("voice_target_section")
        if is_recording:
            return ("REC", "Recording in progress...")
        elif target:
            return ("Ready", f"Target: {target}")
        return ("Ready", "Voice input available")

    elif key == "spec":
        feature_count = len(doc.features) if doc.features else 0
        return (f"{feature_count} features", "Full specification view")

    elif key == "tags":
        has_raw = bool(doc.raw_rant)
        return ("Has data" if has_raw else "Empty", "Raw rant with overlay")

    elif key == "panels":
        statuses = doc.get_section_status()
        complete = sum(1 for s in statuses.values() if s == "complete")
        return (f"{complete}/{len(statuses)}", "All sections at once")

    elif key == "config":
        lab_mode = st.session_state.get("lab_mode_active", False)
        return ("Lab Mode" if lab_mode else "Standard", "Settings & Lab Mode")

    return ("--", "")


def _render_expanded_cockpit_panel(
    panel_key: str,
    db: Session,
    project: "Project",
    doc: "AgentOSDocument",
    session_id: Optional[int]
) -> None:
    """
    Render the expanded content for a cockpit panel.

    Args:
        panel_key: Which panel to expand
        db: Database session
        project: Current project
        doc: AgentOSDocument
        session_id: Optional chat session ID
    """
    # Header with close button
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("Close Panel", key="close_cockpit_panel"):
            del st.session_state["expanded_cockpit_panel"]
            st.rerun()

    # Import panel functions
    from app.ui.agent_os_panel import (
        render_agent_os_tree,
        render_gap_analysis_view,
        render_click_to_rant_panel,
        render_real_time_tagging_panel,
        render_tag_overlay_view,
        render_multi_panel_live_fill,
        render_expanded_section,
        render_export_options,
    )

    # Render appropriate panel content
    if panel_key == "chat":
        st.markdown("### Chat Panel")
        st.info("Chat functionality is available in the main Chat tab.")
        # Could render a mini chat here if needed

    elif panel_key == "tree":
        st.markdown("### Agent OS Tree View")
        render_agent_os_tree(doc)
        st.divider()
        render_export_options(doc)

    elif panel_key == "gaps":
        st.markdown("### Gap Analysis")
        render_gap_analysis_view(doc, db, project)

    elif panel_key == "voice":
        st.markdown("### Voice Input")

        voice_tab = st.radio(
            "Select Mode",
            ["Click-to-Rant", "Real-Time Tagging"],
            horizontal=True,
            key="cockpit_voice_mode"
        )

        if voice_tab == "Click-to-Rant":
            render_click_to_rant_panel(doc, db, project)
        else:
            render_real_time_tagging_panel(doc, db, project)

    elif panel_key == "spec":
        st.markdown("### Full Specification")
        render_agent_os_tree(doc)

    elif panel_key == "tags":
        st.markdown("### Tag Overlay View")
        raw_text = doc.raw_rant if doc.raw_rant else ""

        # Get tagged segments from session if available
        rant_data = st.session_state.get("voice_rant_data", {})
        segments = rant_data.get("segments", [])

        render_tag_overlay_view(doc, raw_text, segments)

    elif panel_key == "panels":
        st.markdown("### Multi-Panel View")
        clicked = render_multi_panel_live_fill(doc)
        if clicked:
            st.session_state.expanded_section = clicked
            st.rerun()

        # Handle section expansion
        if "expanded_section" in st.session_state:
            st.divider()
            render_expanded_section(
                doc,
                st.session_state.expanded_section,
                db,
                project
            )

    elif panel_key == "config":
        st.markdown("### Settings & Lab Mode")
        st.info("Full settings available in the Settings tab. Lab Mode controls shown below.")

        # Quick Lab Mode toggle
        lab_mode = st.toggle(
            "Enable Lab Mode",
            value=st.session_state.get("lab_mode_active", False),
            key="cockpit_lab_mode_toggle"
        )
        st.session_state.lab_mode_active = lab_mode

        if lab_mode:
            st.markdown("**Lab Mode Active**")
            st.caption("Test different feature combinations. See Lab tab for full controls.")


def is_cockpit_mode_active() -> bool:
    """Check if cockpit mode is currently active."""
    return st.session_state.get("cockpit_mode_active", False)


# ============================================================================
# PHASE 5: CONTEXT REFRESH DISPLAY (Mechanism 16)
# ============================================================================


def render_context_refresh(
    db: Session,
    project: Project,
    user_id: int,
) -> bool:
    """
    Render the context refresh panel when returning after time away.

    Shows appropriate refresh content based on time away:
    - < 1 hour: Minimal (just current task)
    - 1-4 hours: Brief (task + recent decisions)
    - 4-24 hours: Medium (session summary + key context)
    - 1-3 days: Full (project overview + session recap)
    - 3-7 days: Extended (full project refresh)
    - 7+ days: Complete (onboarding-style refresh)

    Args:
        db: Database session
        project: Current project
        user_id: Current user ID

    Returns:
        True if refresh was dismissed (ready to work)
    """
    from app.services.session_service import (
        calculate_time_away,
        generate_refresh_content,
        record_activity_ping,
        start_new_session,
        RefreshLevel,
    )

    # Calculate time away
    hours_away, refresh_config = calculate_time_away(db, user_id, project.id)

    # If less than 30 minutes, no refresh needed
    if hours_away < 0.5:
        record_activity_ping(db, user_id, project.id)
        return True

    # Check if refresh was already dismissed this session
    refresh_key = f"refresh_dismissed_{project.id}"
    if st.session_state.get(refresh_key, False):
        return True

    # Generate refresh content
    content = generate_refresh_content(db, user_id, project.id, project)

    # Style based on refresh level
    level = content.get("level", "minimal")
    if level in ["minimal", "brief"]:
        border_color = "#3b82f6"
        bg_gradient = "linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%)"
        icon = "👋"
    elif level in ["medium"]:
        border_color = "#f59e0b"
        bg_gradient = "linear-gradient(135deg, #3a2e1e 0%, #1a1a0a 100%)"
        icon = "📋"
    else:  # full, extended, complete
        border_color = "#8b5cf6"
        bg_gradient = "linear-gradient(135deg, #2e1e5f 0%, #0f0a2a 100%)"
        icon = "🎯"

    # Render refresh panel
    st.markdown(f"""
    <style>
    .refresh-container {{
        background: {bg_gradient};
        border: 2px solid {border_color};
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
    }}
    .refresh-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }}
    .refresh-title {{
        font-size: 24px;
        font-weight: bold;
        color: white;
    }}
    .refresh-time {{
        font-size: 14px;
        color: #94a3b8;
        background: rgba(255, 255, 255, 0.1);
        padding: 4px 12px;
        border-radius: 12px;
    }}
    .refresh-subtitle {{
        font-size: 14px;
        color: #94a3b8;
        margin-bottom: 20px;
    }}
    .refresh-section {{
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }}
    .refresh-section-title {{
        font-size: 14px;
        font-weight: 600;
        color: #e5e7eb;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .refresh-section-content {{
        font-size: 14px;
        color: #94a3b8;
    }}
    .refresh-list {{
        margin: 0;
        padding-left: 20px;
        color: #94a3b8;
    }}
    .refresh-list li {{
        margin-bottom: 4px;
    }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="refresh-container">
        <div class="refresh-header">
            <span class="refresh-title">{icon} {content['title']}</span>
            <span class="refresh-time">Away for {content['time_away']}</span>
        </div>
        <div class="refresh-subtitle">{content['description']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Render sections
    sections = content.get("sections", [])
    for section in sections:
        section_icon = section.get("icon", "📌")
        section_title = section.get("title", "")
        section_content = section.get("content", "")
        section_type = section.get("type", "text")

        with st.container():
            st.markdown(f"**{section_icon} {section_title}**")

            if section_type == "list" and isinstance(section_content, list):
                for item in section_content:
                    st.markdown(f"- {item}")
            else:
                st.markdown(f"_{section_content}_")

            st.markdown("")  # Spacing

    # Action buttons
    st.markdown("")  # Spacing

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if st.button(
            "Continue Working",
            type="primary",
            key="refresh_continue",
            use_container_width=True,
        ):
            # Update activity and dismiss
            start_new_session(db, user_id, project.id)
            st.session_state[refresh_key] = True
            return True

    with col2:
        if st.button(
            "Show More",
            key="refresh_show_more",
            use_container_width=True,
        ):
            # Force full refresh
            st.session_state.force_full_refresh = True
            st.rerun()

    with col3:
        if st.button(
            "Start Fresh",
            key="refresh_start_fresh",
            use_container_width=True,
        ):
            from app.services.session_service import clear_resume_state
            clear_resume_state(db, user_id, project.id)
            st.session_state[refresh_key] = True
            show_info("Starting fresh - previous session state cleared")
            return True

    return False


def render_inline_context_refresh(
    db: Session,
    project: Project,
    user_id: int,
) -> Tuple[bool, Optional[str]]:
    """
    Render a compact inline banner for context refresh.
    NOTE: This is non-blocking - always returns True so page continues to render.

    Returns:
        Tuple of (always True, time_away_str or None)
    """
    from app.services.session_service import (
        calculate_time_away,
        format_time_away,
        record_activity_ping,
        start_new_session,
    )

    # Calculate time away
    hours_away, refresh_config = calculate_time_away(db, user_id, project.id)

    # If less than 30 minutes, no refresh needed
    if hours_away < 0.5:
        record_activity_ping(db, user_id, project.id)
        return True, None

    time_str = format_time_away(hours_away)

    # Check if refresh was already dismissed this session
    refresh_key = f"refresh_dismissed_{project.id}"
    if st.session_state.get(refresh_key, False):
        return True, time_str

    # Show compact inline banner - use wider ratio for button
    col1, col2 = st.columns([3, 1])

    with col1:
        st.info(f"📋 **Session Recap** • Away for {time_str} • Welcome back!")

    with col2:
        if st.button("✓ Continue", key="inline_refresh_continue", type="primary", use_container_width=True):
            start_new_session(db, user_id, project.id)
            st.session_state[refresh_key] = True
            st.rerun()

    # Always return True so page continues to render
    # The banner is just informational, not blocking
    return True, time_str


def render_learning_status_bar(
    db: Session,
    project_id: int,
    user_id: int,
) -> None:
    """
    Render a compact status bar showing Idea Bank and Session status.
    NOTE: This is now integrated into render_compact_status_bar for better layout.
    """
    # This function is kept for backwards compatibility but the
    # compact status bar is now the preferred approach
    pass
