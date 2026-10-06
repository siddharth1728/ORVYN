"""Multi-agent memory, planning, research, opportunities and followups schema.

Revision ID: 002_multi_agent_memory_planning
Revises: 001_initial_schema
Create Date: 2026-10-06
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_multi_agent_memory_planning"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update memories table
    with op.batch_alter_table("memories") as batch_op:
        batch_op.add_column(sa.Column("provenance", sa.JSON(), nullable=False, server_default="{}"))
        batch_op.add_column(sa.Column("embedding", sa.JSON(), nullable=True))

    # 2. Plans
    op.create_table(
        "plans",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("task_id", sa.Uuid(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_plans_task_id", "plans", ["task_id"])

    # 3. Plan Steps
    op.create_table(
        "plan_steps",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("plan_id", sa.Uuid(as_uuid=True), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("tool_name", sa.String(100), nullable=True),
        sa.Column("assigned_agent", sa.String(100), nullable=False, server_default="CoreAgent"),
        sa.Column("dependencies", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("inputs", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("outputs", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False, server_default="120"),
        sa.Column("checkpoint_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_plan_steps_plan_id", "plan_steps", ["plan_id"])
    op.create_index("idx_plan_steps_status", "plan_steps", ["status"])

    # 4. Research Reports
    op.create_table(
        "research_reports",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("task_id", sa.Uuid(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("conflicts_identified", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("uncertainties_and_gaps", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_research_reports_task_id", "research_reports", ["task_id"])

    # 5. Research Sources
    op.create_table(
        "research_sources",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("report_id", sa.Uuid(as_uuid=True), sa.ForeignKey("research_reports.id", ondelete="CASCADE"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_type", sa.String(64), nullable=False, server_default="WEB_SOURCE"),
        sa.Column("reliability_score", sa.Float(), nullable=False, server_default="0.85"),
        sa.Column("content_snippet", sa.Text(), nullable=False, server_default=""),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.create_index("idx_research_sources_report_id", "research_sources", ["report_id"])
    op.create_index("idx_research_sources_domain", "research_sources", ["domain"])

    # 6. Research Findings
    op.create_table(
        "research_findings",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("report_id", sa.Uuid(as_uuid=True), sa.ForeignKey("research_reports.id", ondelete="CASCADE"), nullable=True),
        sa.Column("fact_or_claim", sa.Text(), nullable=False),
        sa.Column("supporting_source_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("conflicting_source_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("is_interpretation", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("idx_research_findings_report_id", "research_findings", ["report_id"])

    # 7. Opportunities
    op.create_table(
        "opportunities",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("organization", sa.String(255), nullable=False),
        sa.Column("opportunity_type", sa.String(64), nullable=False, server_default="INTERNSHIP"),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("is_remote", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("requires_relocation", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("eligibility_criteria", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("required_skills", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("preferred_skills", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("application_url", sa.Text(), nullable=True),
        sa.Column("source_urls", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("canonical_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("status", sa.String(64), nullable=False, server_default="DISCOVERED"),
        sa.Column("score_data", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_opportunities_hash", "opportunities", ["canonical_hash"])
    op.create_index("idx_opportunities_org", "opportunities", ["organization"])
    op.create_index("idx_opportunities_status", "opportunities", ["status"])

    # 8. Follow-Up Targets
    op.create_table(
        "followup_targets",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("task_id", sa.Uuid(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("target_entity", sa.String(255), nullable=False),
        sa.Column("action_to_take", sa.Text(), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(64), nullable=False, server_default="WAITING"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("cooldown_seconds", sa.Integer(), nullable=False, server_default="86400"),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_check_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_followup_targets_task_id", "followup_targets", ["task_id"])
    op.create_index("idx_followup_targets_status", "followup_targets", ["status"])

    # 9. Human Intervention Requests
    op.create_table(
        "human_intervention_requests",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("task_id", sa.Uuid(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("urgency", sa.String(32), nullable=False, server_default="MEDIUM"),
        sa.Column("options", sa.JSON(), nullable=True),
        sa.Column("required_response_type", sa.String(32), nullable=False, server_default="YES_NO"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("resolution", sa.JSON(), nullable=True),
        sa.Column("resolved_by", sa.String(64), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_interventions_task_id", "human_intervention_requests", ["task_id"])
    op.create_index("idx_interventions_status", "human_intervention_requests", ["status"])

    # 10. Agent Handoffs
    op.create_table(
        "agent_handoffs",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("task_id", sa.Uuid(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_agent", sa.String(100), nullable=False),
        sa.Column("to_agent", sa.String(100), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("artifact_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_agent_handoffs_task_id", "agent_handoffs", ["task_id"])

    # 11. Artifacts
    op.create_table(
        "artifacts",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("task_id", sa.Uuid(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("artifact_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_by_agent", sa.String(100), nullable=False, server_default="CoreAgent"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_artifacts_task_id", "artifacts", ["task_id"])
    op.create_index("idx_artifacts_type", "artifacts", ["artifact_type"])


def downgrade() -> None:
    op.drop_table("artifacts")
    op.drop_table("agent_handoffs")
    op.drop_table("human_intervention_requests")
    op.drop_table("followup_targets")
    op.drop_table("opportunities")
    op.drop_table("research_findings")
    op.drop_table("research_sources")
    op.drop_table("research_reports")
    op.drop_table("plan_steps")
    op.drop_table("plans")
    with op.batch_alter_table("memories") as batch_op:
        batch_op.drop_column("embedding")
        batch_op.drop_column("provenance")
