"""empty message

Revision ID: 26e0a88d0729
Revises: 8a21ae799e64
Create Date: 2023-10-22 13:53:20.328393

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26e0a88d0729'
down_revision: Union[str, None] = '8a21ae799e64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('batch', sa.Column('total_files', sa.Integer(), nullable=True))
    op.add_column('batch', sa.Column('processed_files', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('batch', 'processed_files')
    op.drop_column('batch', 'total_files')
    # ### end Alembic commands ###