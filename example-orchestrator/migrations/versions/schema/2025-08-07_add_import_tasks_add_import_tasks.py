"""add Import tasks for devicetype-library.

Revision ID: add_import_tasks
Revises: d946c20663d3
Create Date: 2025-08-07 08:52:00.000000

"""
import sqlalchemy as sa
from alembic import op
from orchestrator.migrations.helpers import delete_workflow
from orchestrator.targets import Target

# revision identifiers, used by Alembic.
revision = "add_import_tasks"
down_revision = "d946c20663d3"
branch_labels = None
depends_on = None

import_tasks = [
    {
        "name": "task_import_vendors",
        "target": Target.SYSTEM,
        "description": "Import Vendors from Devicetype Library",
    },
    {
        "name": "task_import_device_types",
        "target": Target.SYSTEM,
        "description": "Import Device Types from Devicetype Library",
    },
]


def upgrade() -> None:
    conn = op.get_bind()
    for task in import_tasks:
        conn.execute(
            sa.text(
                """INSERT INTO workflows(name, target, description) VALUES (:name, :target, :description)
                   ON CONFLICT DO NOTHING"""
            ),
            task,
        )


def downgrade() -> None:
    conn = op.get_bind()
    for task in import_tasks:
        delete_workflow(conn, task["name"])
