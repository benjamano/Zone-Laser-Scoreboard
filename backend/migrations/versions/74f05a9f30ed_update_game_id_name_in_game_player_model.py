"""update game id name in game player model

Revision ID: 74f05a9f30ed
Revises: 5342edb16084
Create Date: 2025-03-09 11:56:41.245838

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '74f05a9f30ed'
down_revision = '5342edb16084'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('game_player', schema=None) as batch_op:
        batch_op.add_column(sa.Column('gameId', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('gunId', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('playerId', sa.Integer(), nullable=True))

        # Comment these out if they don't exist
        # batch_op.drop_constraint('game_player_gameID_fkey', type_='foreignkey')
        # batch_op.drop_constraint('game_player_gunID_fkey', type_='foreignkey')
        # batch_op.drop_constraint('game_player_playerID_fkey', type_='foreignkey')

        batch_op.create_foreign_key('game_player_gameId_fkey', 'game', ['gameId'], ['id'])
        batch_op.create_foreign_key('game_player_gunId_fkey', 'gun', ['gunId'], ['id'])
        batch_op.create_foreign_key('game_player_playerId_fkey', 'player', ['playerId'], ['id'])

        batch_op.drop_column('gameID')
        batch_op.drop_column('playerID')
        batch_op.drop_column('gunID')


def downgrade():
    # Revert changes back to original naming
    with op.batch_alter_table('game_player', schema=None) as batch_op:
        batch_op.add_column(sa.Column('gameID', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('gunID', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('playerID', sa.Integer(), nullable=True))

        batch_op.drop_constraint('game_player_gameId_fkey', type_='foreignkey')
        batch_op.drop_constraint('game_player_gunId_fkey', type_='foreignkey')
        batch_op.drop_constraint('game_player_playerId_fkey', type_='foreignkey')

        batch_op.create_foreign_key('game_player_gameID_fkey', 'game', ['gameID'], ['id'])
        batch_op.create_foreign_key('game_player_gunID_fkey', 'gun', ['gunID'], ['id'])
        batch_op.create_foreign_key('game_player_playerID_fkey', 'player', ['playerID'], ['id'])

        batch_op.drop_column('gameId')
        batch_op.drop_column('gunId')
        batch_op.drop_column('playerId')

    # ### end Alembic commands ###
