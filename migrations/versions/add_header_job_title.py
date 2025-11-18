"""Add header_job_title column to resumes

Revision ID: header_job_title_001
Revises: 
Create Date: 2025-11-11 22:43:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'header_job_title_001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add header_job_title column to resumes table
    with op.batch_alter_table('resumes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('header_job_title', sa.String(length=200), nullable=True))

def downgrade():
    # Remove header_job_title column from resumes table
    with op.batch_alter_table('resumes', schema=None) as batch_op:
        batch_op.drop_column('header_job_title')