from sqlalchemy import select
from sqlalchemy.orm import joinedload
from core import get_session
from models import User, PlayerStats, UserRole, RoleType

def get_club_stats_ranking(club_id: int):
    with get_session as session:
        stmt = (
            select(User)
            .options(joinedload(User.stats))
            .join(UserRole, User.id == UserRole.user_id)
            .where(
                User.club_id == club_id,
                UserRole.role == RoleType.PLAYER,
            )
            .order_by(User.number.asc().nullslast())
        )
        users = session.scalars(stmt).unique().all()
        for u in users:
            session.expunge(u)
        return users

def get_or_create_player_stats(user_id: int) -> PlayerStats:
    with get_session() as session:
        stats = session.scalars(select(PlayerStats).where(PlayerStats.player_id == user_id)).first()
        if not stats:
            stats = PlayerStats(player_id=user_id)
            session.add(stats)
            session.commit()
            session.refresh(stats)
        session.expunge(stats)
        return stats