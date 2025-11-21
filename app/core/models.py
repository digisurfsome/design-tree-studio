"""
SQLAlchemy models for Design Tree Studio.

This module contains all database models/tables for the application.
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Boolean,
    ForeignKey,
    JSON,
    Float,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from app.core.db import Base


# Enums for model fields
class NodeStatus(str, enum.Enum):
    """Status of a node in the design tree."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"
    DELETED = "deleted"


class DescriptionMode(str, enum.Enum):
    """Mode for project description."""
    MANUAL = "manual"      # Use only manual description
    AUTO = "auto"          # Use only auto-generated description
    MERGE = "merge"        # Merge manual and auto descriptions


class NodeType(str, enum.Enum):
    """Type of node in the design tree."""
    ROOT = "root"
    FOLDER = "folder"
    COMPONENT = "component"
    ASSET = "asset"
    NOTE = "note"


class MessageRole(str, enum.Enum):
    """Role of a chat message."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SessionStatus(str, enum.Enum):
    """Status of a chat session."""
    ACTIVE = "active"              # Normal active session
    WARMING = "warming"            # Warm-up in progress
    WARMED_PENDING = "warmed_pending"  # Warm-up complete, ready to use
    ARCHIVED = "archived"          # Archived session


# Base mixin for common fields
class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


# Models
class UserProfile(Base, TimestampMixin):
    """
    User profile information.

    Stores basic user information and preferences.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    preferences: Mapped[Optional[dict]] = mapped_column(JSON)  # Store user preferences as JSON

    # Relationships
    projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="owner", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        "ChatSession", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<UserProfile(id={self.id}, username='{self.username}', email='{self.email}')>"


class Project(Base, TimestampMixin):
    """
    Design project.

    Represents a design project containing nodes, contexts, and related data.
    """
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tags: Mapped[Optional[list]] = mapped_column(JSON)  # Array of tags
    extra_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON)  # Additional project metadata

    # Relationships
    owner: Mapped["UserProfile"] = relationship("UserProfile", back_populates="projects")
    contexts: Mapped[list["ProjectContext"]] = relationship(
        "ProjectContext", back_populates="project", cascade="all, delete-orphan"
    )
    nodes: Mapped[list["Node"]] = relationship(
        "Node", back_populates="project", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        "ChatSession", back_populates="project", cascade="all, delete-orphan"
    )
    batons: Mapped[list["BatonSnapshot"]] = relationship(
        "BatonSnapshot", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', owner_id={self.owner_id})>"


class ProjectContext(Base, TimestampMixin):
    """
    Context information for a project.

    Stores contextual information, guidelines, and AI instructions for a project.
    """
    __tablename__ = "project_contexts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    context_type: Mapped[str] = mapped_column(String(50), default="general")  # general, design_system, guidelines, etc.
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Auto-generated description (Phase 7)
    auto_description: Mapped[Optional[str]] = mapped_column(Text)

    # Description mode selector (Phase 7)
    description_mode: Mapped[DescriptionMode] = mapped_column(
        SQLEnum(DescriptionMode),
        default=DescriptionMode.MANUAL,
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)  # For ordering contexts
    extra_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="contexts")

    def __repr__(self):
        return f"<ProjectContext(id={self.id}, project_id={self.project_id}, name='{self.name}')>"


class Node(Base, TimestampMixin):
    """
    Node in the design tree.

    Represents a hierarchical node that can be a component, asset, folder, etc.
    """
    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("nodes.id"), index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    node_type: Mapped[NodeType] = mapped_column(SQLEnum(NodeType), nullable=False, default=NodeType.COMPONENT)
    status: Mapped[NodeStatus] = mapped_column(SQLEnum(NodeStatus), nullable=False, default=NodeStatus.ACTIVE)

    description: Mapped[Optional[str]] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, default=0)  # For ordering siblings
    path: Mapped[Optional[str]] = mapped_column(String(1000))  # Materialized path for hierarchical queries

    # Current version reference
    current_version_id: Mapped[Optional[int]] = mapped_column(Integer)  # References latest NodeVersion

    tags: Mapped[Optional[list]] = mapped_column(JSON)
    extra_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="nodes")
    parent: Mapped[Optional["Node"]] = relationship(
        "Node", remote_side=[id], back_populates="children"
    )
    children: Mapped[list["Node"]] = relationship(
        "Node", back_populates="parent", cascade="all, delete-orphan"
    )
    versions: Mapped[list["NodeVersion"]] = relationship(
        "NodeVersion", back_populates="node", cascade="all, delete-orphan"
    )
    draft_meta: Mapped[Optional["DraftMeta"]] = relationship(
        "DraftMeta", back_populates="node", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Node(id={self.id}, name='{self.name}', type='{self.node_type}', status='{self.status}')>"


class NodeVersion(Base, TimestampMixin):
    """
    Version of a node.

    Stores historical versions of node content and configuration.
    """
    __tablename__ = "node_versions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)

    content: Mapped[Optional[str]] = mapped_column(Text)  # Main content (code, text, etc.)
    content_type: Mapped[str] = mapped_column(String(50), default="text")  # text, json, html, etc.

    # Version metadata
    change_summary: Mapped[Optional[str]] = mapped_column(Text)
    author: Mapped[Optional[str]] = mapped_column(String(255))
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)

    # AI-generated fields
    ai_summary: Mapped[Optional[str]] = mapped_column(Text)
    ai_metadata: Mapped[Optional[dict]] = mapped_column(JSON)

    extra_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON)

    # Relationships
    node: Mapped["Node"] = relationship("Node", back_populates="versions")

    def __repr__(self):
        return f"<NodeVersion(id={self.id}, node_id={self.node_id}, version={self.version_number})>"


class DraftMeta(Base, TimestampMixin):
    """
    Draft metadata for nodes.

    Stores draft-specific information and AI-generated content for nodes.
    """
    __tablename__ = "draft_metas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id"), unique=True, nullable=False, index=True)

    draft_content: Mapped[Optional[str]] = mapped_column(Text)
    draft_notes: Mapped[Optional[str]] = mapped_column(Text)

    # AI analysis and suggestions
    ai_suggestions: Mapped[Optional[list]] = mapped_column(JSON)
    ai_analysis: Mapped[Optional[dict]] = mapped_column(JSON)

    # Draft status
    is_reviewing: Mapped[bool] = mapped_column(Boolean, default=False)
    last_ai_update: Mapped[Optional[datetime]] = mapped_column(DateTime)

    extra_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON)

    # Relationships
    node: Mapped["Node"] = relationship("Node", back_populates="draft_meta")

    def __repr__(self):
        return f"<DraftMeta(id={self.id}, node_id={self.node_id})>"


class RantSummary(Base, TimestampMixin):
    """
    Summary of user rants/discussions.

    Stores AI-generated summaries of user discussions and brainstorming sessions.
    """
    __tablename__ = "rant_summaries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    original_content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    # Extracted information
    key_points: Mapped[Optional[list]] = mapped_column(JSON)
    action_items: Mapped[Optional[list]] = mapped_column(JSON)
    tags: Mapped[Optional[list]] = mapped_column(JSON)

    # AI metadata
    sentiment: Mapped[Optional[str]] = mapped_column(String(50))
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)

    extra_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON)

    def __repr__(self):
        return f"<RantSummary(id={self.id}, title='{self.title}')>"


class ChatSession(Base, TimestampMixin):
    """
    Chat session with AI.

    Represents a conversation thread with the AI assistant.
    """
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)

    # Session status (for warm-up workflow)
    status: Mapped[SessionStatus] = mapped_column(
        SQLEnum(SessionStatus),
        default=SessionStatus.ACTIVE,
        nullable=False
    )

    # Session context
    context_snapshot: Mapped[Optional[dict]] = mapped_column(JSON)  # Snapshot of relevant context
    session_type: Mapped[str] = mapped_column(String(50), default="general")  # general, design_review, brainstorm, etc.

    # Token tracking
    total_prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    extra_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON)

    # Relationships
    user: Mapped["UserProfile"] = relationship("UserProfile", back_populates="chat_sessions")
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at"
    )

    def __repr__(self):
        return f"<ChatSession(id={self.id}, title='{self.title}', user_id={self.user_id})>"


class ChatMessage(Base, TimestampMixin):
    """
    Individual message in a chat session.

    Stores messages exchanged between user and AI assistant.
    """
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"), nullable=False, index=True)

    role: Mapped[MessageRole] = mapped_column(SQLEnum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Warm-up flag
    is_warmup: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Message metadata
    token_count: Mapped[Optional[int]] = mapped_column(Integer)
    model_used: Mapped[Optional[str]] = mapped_column(String(100))

    # For assistant messages
    function_call: Mapped[Optional[dict]] = mapped_column(JSON)

    extra_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON)

    # Relationships
    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, session_id={self.session_id}, role='{self.role}')>"


class BatonSnapshot(Base, TimestampMixin):
    """
    Snapshot of application state (baton).

    Stores point-in-time snapshots of project state for versioning and rollback.
    """
    __tablename__ = "baton_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)

    snapshot_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Snapshot content (AI-generated markdown description)
    snapshot_body: Mapped[str] = mapped_column(Text, nullable=False)

    # Snapshot data
    state_data: Mapped[dict] = mapped_column(JSON, nullable=False)  # Complete state snapshot

    # Snapshot metadata
    snapshot_type: Mapped[str] = mapped_column(String(50), default="manual")  # manual, auto, checkpoint
    created_by: Mapped[Optional[str]] = mapped_column(String(255))

    # Hash for integrity checking
    state_hash: Mapped[Optional[str]] = mapped_column(String(64))

    extra_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON)

    # Relationships
    session: Mapped["ChatSession"] = relationship("ChatSession")
    user: Mapped["UserProfile"] = relationship("UserProfile")
    project: Mapped["Project"] = relationship("Project", back_populates="batons")

    def __repr__(self):
        return f"<BatonSnapshot(id={self.id}, project_id={self.project_id}, name='{self.snapshot_name}')>"


class Settings(Base, TimestampMixin):
    """
    Application settings.

    Stores global and user-specific application settings.
    """
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True)

    setting_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    setting_value: Mapped[Optional[str]] = mapped_column(Text)
    setting_type: Mapped[str] = mapped_column(String(50), default="string")  # string, int, bool, json

    is_global: Mapped[bool] = mapped_column(Boolean, default=False)  # Global vs user-specific
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=False)

    description: Mapped[Optional[str]] = mapped_column(String(500))
    extra_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON)

    def __repr__(self):
        return f"<Settings(id={self.id}, key='{self.setting_key}', global={self.is_global})>"
