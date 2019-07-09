"""rostertwotwo

Revision ID: 123dc68dd1ff
Revises: b4fd86f3c4a3
Create Date: 2019-06-10 16:11:52.541067

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '123dc68dd1ff'
down_revision = 'b4fd86f3c4a3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('player', sa.Column('last_activity_time', sa.DateTime(), nullable=True))
    op.drop_column('player', 'last_activeity_time')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('player', sa.Column('last_activeity_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.drop_column('player', 'last_activity_time')
    # ### end Alembic commands ###
