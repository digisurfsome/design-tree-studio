"""
Design Tree Studio - Main Streamlit Application

This is the entry point for the Streamlit application.
"""

import streamlit as st
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config.settings import settings
from app.core.db import (
    test_connection,
    initialize_schema,
    check_tables_exist,
    get_db,
)
from app.ui.layout import (
    render_header,
    render_footer,
    show_success,
    show_error,
    show_warning,
    show_info,
    render_user_selector,
    render_project_selector,
    render_create_project_form,
    render_settings_ui,
    render_project_context_ui,
    render_chat_panel,
    render_truth_doc_export_ui,
    render_cockpit_mode_toggle,
    render_cockpit_dashboard,
    is_cockpit_mode_active,
    render_context_refresh,
    render_learning_status_bar,
    inject_compact_css,
    render_compact_status_bar,
    render_inline_context_refresh,
)
from app.ui.node_tree_panel import render_design_tree_panel
from app.ui.roundtable_panel import render_roundtable_panel
from app.ui.agent_os_panel import render_agent_os_panel
from app.ui.lab_panel import render_lab_panel, render_lab_mode_indicator
from app.ui.idea_bank_panel import (
    render_warmup_modal,
    render_idea_bank_panel,
)
from app.services import (
    get_or_create_default_user,
    list_all_users,
)


def init_session_state():
    """Initialize session state variables."""
    if "show_create_project" not in st.session_state:
        st.session_state.show_create_project = False
    if "pin_verified" not in st.session_state:
        st.session_state.pin_verified = False
    if "pin_attempts" not in st.session_state:
        st.session_state.pin_attempts = 0


def check_pin_lock():
    """
    Check if PIN lock is enabled and verify PIN.

    Returns:
        bool: True if PIN is not required or verified, False otherwise
    """
    # Try to get PIN from settings
    try:
        with get_db() as db:
            from app.services import get_setting
            pin_code = get_setting(db, "pin_code")

            # No PIN set, allow access
            if not pin_code or pin_code.strip() == "":
                st.session_state.pin_verified = True
                return True

            # PIN already verified in this session
            if st.session_state.get("pin_verified", False):
                return True

            # Show PIN entry form
            st.title("🔒 PIN Required")
            st.info("This application is protected with a PIN. Please enter the PIN to continue.")

            col1, col2, col3 = st.columns([1, 2, 1])

            with col2:
                pin_input = st.text_input(
                    "Enter PIN",
                    type="password",
                    key="pin_input",
                    placeholder="Enter your PIN code"
                )

                col_a, col_b = st.columns(2)

                with col_a:
                    if st.button("Unlock", type="primary", use_container_width=True):
                        if pin_input == pin_code:
                            st.session_state.pin_verified = True
                            st.session_state.pin_attempts = 0
                            show_success("PIN verified! Access granted.")
                            st.rerun()
                        else:
                            st.session_state.pin_attempts += 1
                            show_error(f"Incorrect PIN. Attempt {st.session_state.pin_attempts}")

                            if st.session_state.pin_attempts >= 3:
                                st.warning("Multiple failed attempts detected. Please check your PIN configuration.")

                with col_b:
                    if st.button("Exit", use_container_width=True):
                        st.stop()

            # Show hint after multiple attempts
            if st.session_state.pin_attempts >= 3:
                with st.expander("ℹ️ Need Help?"):
                    st.markdown("""
                    **To reset or change the PIN:**

                    1. Access the database directly and update the `settings` table
                    2. Set `pin_code` to empty string to disable PIN lock
                    3. Or set a new PIN value

                    **For development:**
                    - Check your Settings in the database
                    - PIN is stored in the `settings` table with key `pin_code`
                    """)

            return False

    except Exception as e:
        # If we can't check PIN (e.g., DB not initialized), allow access
        st.session_state.pin_verified = True
        return True


def render_system_status():
    """Render the system status tab."""
    st.header("System Status")

    # Check configuration - now checks both env vars AND database settings
    st.subheader("Configuration Status")

    # Get database API key if available
    db_openai_key = ""
    openai_source = None
    try:
        with get_db() as db:
            from app.services import get_setting
            db_openai_key = get_setting(db, "OPENAI_API_KEY") or ""
    except Exception:
        pass

    # Determine OpenAI key source
    if settings.OPENAI_API_KEY:
        openai_source = "environment"
    elif db_openai_key:
        openai_source = "database"

    # Check if all required config is present
    has_openai_key = bool(settings.OPENAI_API_KEY) or bool(db_openai_key)
    has_database = bool(settings.DATABASE_URL)

    if has_database and has_openai_key:
        show_success("All required configuration is present")
    else:
        show_error("Configuration incomplete")
        if not has_database:
            st.markdown("- DATABASE_URL is not configured")
        if not has_openai_key:
            st.markdown("- OPENAI_API_KEY is not configured (set in Settings tab or environment)")
        show_warning(
            "Please configure the required variables in Settings tab or environment. "
            "See `.env.example` for reference."
        )

    # Test database connection
    st.subheader("Database Connection")

    if not settings.DATABASE_URL:
        show_warning(
            "Database not configured. Please set DATABASE_URL in your .env file."
        )
        st.code(
            """
# Example .env file:
DATABASE_URL=postgresql://user:password@host/database
OPENAI_API_KEY=sk-...
            """,
            language="bash",
        )
    else:
        with st.spinner("Testing database connection..."):
            success, message = test_connection()

            if success:
                show_success(message)
                st.info("✅ Database is ready for use!")
            else:
                show_error(message)
                st.markdown(
                    """
                    **Troubleshooting tips:**
                    - Verify your DATABASE_URL is correct
                    - Ensure your database is running and accessible
                    - Check network connectivity
                    - For Neon, ensure your connection string includes SSL parameters
                    """
                )

    # Database Schema Status
    st.subheader("Database Schema")

    if settings.DATABASE_URL:
        try:
            tables_exist, existing_tables = check_tables_exist()

            # Check for all required tables including roundtable tables and Phase 5 tables
            required_tables = [
                "user_profiles", "projects", "project_contexts", "nodes",
                "node_versions", "draft_meta", "rant_summaries", "chat_sessions",
                "chat_messages", "baton_snapshots", "settings",
                "roundtable_sessions", "roundtable_rounds",
                "roundtable_agents", "roundtable_responses",
                "raw_rants",
                # Phase 5: Learning & Memory
                "ideas", "session_activities"
            ]
            missing_tables = [t for t in required_tables if t not in existing_tables]
            all_tables_exist = len(missing_tables) == 0

            if tables_exist and len(existing_tables) > 0:
                if all_tables_exist:
                    show_success(
                        f"Database schema is fully initialized ({len(existing_tables)} tables found)"
                    )
                else:
                    show_warning(
                        f"Database schema partially initialized - {len(missing_tables)} tables missing"
                    )
                    st.markdown("**Missing tables:** " + ", ".join(f"`{t}`" for t in missing_tables))
                    st.info("Click 'Initialize Schema' to create the missing tables.")

                with st.expander("View existing tables"):
                    for table in sorted(existing_tables):
                        st.markdown(f"- `{table}`")
            else:
                show_warning("Database schema not initialized")
                st.markdown(
                    """
                    The database is connected but no tables have been created yet.
                    Click the button below to initialize the database schema.
                    """
                )

            # Initialize schema button - enabled if any tables are missing
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button(
                    "Initialize Schema",
                    type="primary",
                    disabled=all_tables_exist,
                ):
                    with st.spinner("Creating database tables..."):
                        success, message = initialize_schema()

                        if success:
                            show_success(message)
                            st.rerun()
                        else:
                            show_error(message)

            with col2:
                if st.button("Refresh Status"):
                    st.rerun()

        except Exception as e:
            show_error(f"Error checking schema status: {str(e)}")
    else:
        show_warning("Configure DATABASE_URL to initialize schema")

    # OpenAI configuration status
    st.subheader("OpenAI Configuration")

    # Re-check database for OpenAI key (in case it was updated)
    db_key_check = ""
    db_model = ""
    try:
        with get_db() as db:
            from app.services import get_setting
            db_key_check = get_setting(db, "OPENAI_API_KEY") or ""
            db_model = get_setting(db, "DEFAULT_CHAT_MODEL") or settings.OPENAI_MODEL
    except Exception:
        db_model = settings.OPENAI_MODEL

    if settings.OPENAI_API_KEY:
        show_success("OpenAI API key is configured (from environment)")
        st.info(f"Using model: {settings.OPENAI_MODEL}")
    elif db_key_check:
        show_success("OpenAI API key is configured (from Settings)")
        st.info(f"Using model: {db_model}")
    else:
        show_warning("OpenAI API key not configured - set it in the Settings tab")

    # Development info
    if settings.DEBUG:
        st.subheader("Debug Information")
        with st.expander("Show Debug Info"):
            debug_info = {
                "APP_NAME": settings.APP_NAME,
                "APP_VERSION": settings.APP_VERSION,
                "DEBUG": settings.DEBUG,
                "DATABASE_CONFIGURED": bool(settings.DATABASE_URL),
                "OPENAI_CONFIGURED": bool(settings.OPENAI_API_KEY),
                "OPENAI_MODEL": settings.OPENAI_MODEL,
            }

            if settings.DATABASE_URL:
                tables_exist, existing_tables = check_tables_exist()
                debug_info["TABLES_COUNT"] = len(existing_tables)
                debug_info["TABLES"] = existing_tables

            st.json(debug_info)

        # Model information
        with st.expander("Show Database Models"):
            st.markdown(
                """
            **Implemented Models:**
            - `UserProfile` - User accounts and profiles
            - `Project` - Design projects
            - `ProjectContext` - Project context and guidelines
            - `Node` - Hierarchical design tree nodes
            - `NodeVersion` - Version history for nodes
            - `DraftMeta` - Draft metadata and AI suggestions
            - `RantSummary` - AI-generated summaries of discussions
            - `ChatSession` - AI chat conversation sessions
            - `ChatMessage` - Individual chat messages
            - `BatonSnapshot` - Project state snapshots
            - `Settings` - Application and user settings
            """
            )


def main():
    """Main application entry point."""

    # Page configuration
    st.set_page_config(
        page_title=settings.APP_NAME,
        page_icon="🎨",
        layout="wide",
        initial_sidebar_state="collapsed",  # Start collapsed for more space
    )

    # Inject compact CSS for tight layout
    inject_compact_css()

    # Initialize session state
    init_session_state()

    # Check PIN lock (Phase 8)
    if not check_pin_lock():
        # PIN not verified, show PIN form only
        render_footer()
        return

    # NO BIG HEADER - we use compact status bar instead

    # Check database connection first
    if not settings.DATABASE_URL:
        show_error("Database not configured. Please set DATABASE_URL in your .env file.")
        render_footer()
        return

    # Check if schema is initialized
    tables_exist, existing_tables = check_tables_exist()
    if not tables_exist or len(existing_tables) == 0:
        show_warning("Database schema not initialized. Please go to System Status tab to initialize.")
        st.info("Click 'System Status' tab below and use the 'Initialize Schema' button.")

        # Show system status tab for initialization
        tab1, tab2, tab3 = st.tabs(["System Status", "Settings", "Project Context"])

        with tab1:
            render_system_status()

        with tab2:
            st.info("Initialize database schema first to use Settings.")

        with tab3:
            st.info("Initialize database schema first to use Project Context.")

        render_footer()
        return

    # Main application with user/project selection
    with st.sidebar:
        st.header("👤 User & Project")

        # User selection with database session
        with get_db() as db:
            # Get or create default user
            default_user = get_or_create_default_user(db)
            all_users = list_all_users(db)

            # User selector
            current_user = render_user_selector(db, all_users)

            if not current_user:
                show_error("Please select a user")
                return

            st.divider()

            # Project selector
            if st.session_state.show_create_project:
                # Show create project form
                new_project = render_create_project_form(db, current_user)
                if new_project:
                    st.session_state.show_create_project = False
                    st.session_state.current_project_id = new_project.id
                    st.session_state.current_project_name = new_project.name
                    st.rerun()
            else:
                # Show project selector
                selected_project, should_create = render_project_selector(db, current_user)

                if should_create:
                    st.session_state.show_create_project = True
                    st.rerun()

                # Store selected project in session state
                if selected_project:
                    st.session_state.current_project_id = selected_project.id
                    st.session_state.current_project_name = selected_project.name

                    # Show project info
                    with st.expander("ℹ️ Project Info"):
                        st.markdown(f"**Name:** {selected_project.name}")
                        if selected_project.description:
                            st.markdown(f"**Description:** {selected_project.description}")
                        st.markdown(f"**Owner:** {current_user.username}")
                        st.markdown(f"**Created:** {selected_project.created_at.strftime('%Y-%m-%d')}")

        st.divider()
        st.caption(f"{settings.APP_NAME} v{settings.APP_VERSION}")

    # =========================================================================
    # COMPACT LAYOUT: Status bar at top, then columns
    # =========================================================================

    # Get project and user info for status bar
    project = None
    time_away_str = None
    ideas_count = 0
    is_ready = True

    if st.session_state.get("current_project_id") and "current_user" in locals() and current_user:
        with get_db() as db:
            from app.services import get_project_by_id
            from app.services.idea_bank_service import get_idea_stats
            from app.services.session_service import needs_warmup, calculate_time_away, format_time_away

            project = get_project_by_id(db, st.session_state.current_project_id)
            if project:
                # Get stats for status bar
                try:
                    stats = get_idea_stats(db, project.id, current_user.id)
                    ideas_count = stats.get('active', 0)
                    is_ready = not needs_warmup(db, current_user.id, project.id)
                    hours_away, _ = calculate_time_away(db, current_user.id, project.id)
                    if hours_away >= 0.5:
                        time_away_str = format_time_away(hours_away)
                except Exception:
                    pass

                # Render compact status bar at TOP (above columns)
                render_compact_status_bar(
                    project_name=project.name,
                    is_ready=is_ready,
                    ideas_count=ideas_count,
                    time_away_str=time_away_str,
                )

    # Main content area with columns (chat on left, tabs on right)
    chat_col, main_col = st.columns([1, 2])

    # Left column: Chat panel
    with chat_col:
        if st.session_state.get("current_project_id") and "current_user" in locals() and current_user:
            with get_db() as db:
                from app.services import get_project_by_id
                from app.services.session_service import record_activity_ping

                project = get_project_by_id(db, st.session_state.current_project_id)
                if project:
                    # Phase 5: Show warmup modal if needed (before anything else)
                    warmup_key = f"warmup_shown_{project.id}"
                    if not st.session_state.get(warmup_key, False):
                        warmup_dismissed = render_warmup_modal(db, project.id, current_user.id)
                        if warmup_dismissed:
                            st.session_state[warmup_key] = True
                            st.rerun()
                        else:
                            # Still showing warmup, don't render anything else
                            st.stop()

                    # Phase 5: Compact inline context refresh (non-blocking)
                    render_inline_context_refresh(db, project, current_user.id)

                    # Record activity ping
                    record_activity_ping(db, current_user.id, project.id)

                    # Render the main chat panel (no extra status bar needed)
                    render_chat_panel(db, current_user.id, project)
                else:
                    st.warning("⚠️ Project not found. Select one from sidebar.")
        else:
            st.info("📁 Select a project from the sidebar to start.")

    # Right column: Tabs
    with main_col:
        # Check for Cockpit Mode
        cockpit_active = is_cockpit_mode_active()

        # Compact mode toggle row
        mode_col1, mode_col2 = st.columns([4, 1])
        with mode_col2:
            render_cockpit_mode_toggle()
        with mode_col1:
            render_lab_mode_indicator()

        # If Cockpit Mode is active, show the dashboard instead of tabs
        if cockpit_active and st.session_state.get("current_project_id"):
            with get_db() as db:
                from app.services import get_project_by_id
                project = get_project_by_id(db, st.session_state.current_project_id)
                if project:
                    session_id = st.session_state.get("current_chat_session_id")
                    render_cockpit_dashboard(db, project, session_id)
                else:
                    show_error("Project not found")
        else:
            # Standard tabs mode
            tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs(
                ["🏠 System Status", "⚙️ Settings", "📋 Project Context", "🎨 Design Tree", "🤖 Agent OS", "💡 Idea Bank", "🧪 Lab Mode", "📄 Truth Doc", "📊 Process Log", "🔄 Roundtable"]
            )

            with tab1:
                render_system_status()

            with tab2:
                if "current_user" in locals() and current_user:
                    with get_db() as db:
                        render_settings_ui(db, user_id=None)  # Global settings for now
                else:
                    st.info("Select a user to configure settings.")

            with tab3:
                if st.session_state.get("current_project_id"):
                    with get_db() as db:
                        from app.services import get_project_by_id

                        project = get_project_by_id(db, st.session_state.current_project_id)
                        if project:
                            render_project_context_ui(db, project)
                        else:
                            show_error("⚠️ Selected project not found. Please select a project from the sidebar.")
                else:
                    st.info("📁 **No Project Selected**\n\nPlease select or create a project in the left sidebar to manage project context.")

            with tab4:
                if st.session_state.get("current_project_id"):
                    with get_db() as db:
                        from app.services import get_project_by_id

                        project = get_project_by_id(db, st.session_state.current_project_id)
                        if project:
                            render_design_tree_panel(db, project)
                        else:
                            show_error("⚠️ Selected project not found. Please select a project from the sidebar.")
                else:
                    st.info("📁 **No Project Selected**\n\nPlease select or create a project in the left sidebar to manage design tree nodes.")

            with tab5:
                # Agent OS - Transform rants into structured specs
                if st.session_state.get("current_project_id"):
                    with get_db() as db:
                        from app.services import get_project_by_id

                        project = get_project_by_id(db, st.session_state.current_project_id)
                        if project:
                            # Get current chat session ID if available
                            session_id = st.session_state.get("current_chat_session_id")
                            render_agent_os_panel(db, project, session_id)
                        else:
                            show_error("⚠️ Selected project not found. Please select a project from the sidebar.")
                else:
                    st.info("📁 **No Project Selected**\n\nPlease select or create a project in the left sidebar to use Agent OS.")

            with tab6:
                # Idea Bank - Phase 5 Learning & Memory
                if st.session_state.get("current_project_id"):
                    with get_db() as db:
                        from app.services import get_project_by_id

                        project = get_project_by_id(db, st.session_state.current_project_id)
                        if project and current_user:
                            render_idea_bank_panel(db, project, current_user.id)
                        else:
                            show_error("⚠️ Selected project not found. Please select a project from the sidebar.")
                else:
                    st.info("📁 **No Project Selected**\n\nPlease select or create a project in the left sidebar to use Idea Bank.")

            with tab7:
                # Lab Mode - Test different feature combinations
                if st.session_state.get("current_project_id"):
                    with get_db() as db:
                        from app.services import get_project_by_id

                        project = get_project_by_id(db, st.session_state.current_project_id)
                        if project:
                            render_lab_panel(db, project)
                        else:
                            show_error("⚠️ Selected project not found. Please select a project from the sidebar.")
                else:
                    st.info("📁 **No Project Selected**\n\nPlease select or create a project in the left sidebar to use Lab Mode.")

            with tab8:
                if st.session_state.get("current_project_id"):
                    with get_db() as db:
                        from app.services import get_project_by_id

                        project = get_project_by_id(db, st.session_state.current_project_id)
                        if project:
                            render_truth_doc_export_ui(db, project)
                        else:
                            show_error("⚠️ Selected project not found. Please select a project from the sidebar.")
                else:
                    st.info("📁 **No Project Selected**\n\nPlease select or create a project in the left sidebar to export Truth Doc.")

            with tab9:
                from app.services import render_process_log
                render_process_log()

            with tab10:
                # Roundtable Coder - works with or without a project
                with get_db() as db:
                    project_id = st.session_state.get("current_project_id")
                    render_roundtable_panel(db, project_id=project_id)

    # Render footer
    render_footer()


if __name__ == "__main__":
    main()
