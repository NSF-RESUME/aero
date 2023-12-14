"""Add timer to provenance

Revision ID: 1d0d14a01872
Revises: ba24f021ed5a
Create Date: 2023-12-14 07:36:02.288322

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1d0d14a01872"
down_revision = "ba24f021ed5a"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("provenance", schema=None) as batch_op:
        batch_op.add_column(sa.Column("timer", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("timer_job_id", sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("provenance", schema=None) as batch_op:
        batch_op.drop_column("timer_job_id")
        batch_op.drop_column("timer")

    # ### end Alembic commands ###
