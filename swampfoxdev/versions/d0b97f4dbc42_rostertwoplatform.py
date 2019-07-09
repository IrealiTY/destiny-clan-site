"""rostertwoplatform

Revision ID: d0b97f4dbc42
Revises: 123dc68dd1ff
Create Date: 2019-06-10 16:36:29.669951

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd0b97f4dbc42'
down_revision = '123dc68dd1ff'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('player', sa.Column('membership_type', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('player', 'membership_type')
    # ### end Alembic commands ###
