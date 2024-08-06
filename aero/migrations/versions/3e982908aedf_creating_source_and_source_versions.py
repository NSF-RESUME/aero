"""Creating source and source versions

Revision ID: 3e982908aedf
Revises:
Create Date: 2023-06-23 22:34:06.153179

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3e982908aedf"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "source",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("timer", sa.Integer(), nullable=True),
        sa.Column("verifier", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "source_version",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column("checksum", sa.String(), nullable=True),
        sa.Column("proxy_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.Date(), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["source.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("source_version")
    op.drop_table("source")
    # ### end Alembic commands ###
