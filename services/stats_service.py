from sqlalchemy import select, update
from sqlalchemy.orm import joinedload
from core import get_session
from models import User, PlayerStats, UserRole, RoleType

VALID_STATS = {
    'matches_played': PlayerStats.matches_played,
    'starter_amount': PlayerStats.starter_amount,
    'goals': PlayerStats.goals,
    'assists': PlayerStats.assists,
    'yellow_cards': PlayerStats.yellow_cards,
    'red_cards': PlayerStats.red_cards,
    'mvp_count': PlayerStats.mvp_count,
}

def get_club_stats_ranking(club_id: int):
    with get_session() as session:
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

def get_player_stats(player_id: int) -> PlayerStats:
    with get_session() as session:
        stats = session.scalars(select(PlayerStats).where(PlayerStats.player_id == player_id)).first()
        if not stats:
            stats = PlayerStats(player_id=player_id)
            session.add(stats)
            session.commit()
            session.refresh(stats)
        session.expunge(stats)
        return stats

def update_player_stats(
    player_id: int,
    matches_played: int, 
    starter_amount: int, 
    goals: int, 
    assists: int, 
    yellow_cards: int, 
    red_cards: int,
    mvp_count: int
) -> PlayerStats:
    with get_session() as session:
        stats = session.scalars(select(PlayerStats).where(PlayerStats.player_id == player_id)).first()
        if not stats:
            stats = PlayerStats(player_id=player_id)
            session.add(stats)

        stats.matches_played = matches_played
        stats.starter_amount = starter_amount
        stats.goals = goals
        stats.assists = assists
        stats.yellow_cards = yellow_cards
        stats.red_cards = red_cards
        stats.mvp_count = mvp_count
        
        session.commit()
        session.refresh(stats)
        session.expunge(stats)
        return stats

def increment_stat(club_id: int, player_ids: list[int], stat: str) -> int:
    if not stat or stat not in VALID_STATS:
        raise ValueError("error_stat_invalid")
    
    if not player_ids:
        raise ValueError("error_no_players_selected")

    with get_session() as session:
        players = session.scalars(
            select(User).where(User.id.in_(player_ids), User.club_id == club_id)
        ).all()
        
        found_ids = {p.id for p in players}
        invalid_ids = set(player_ids) - found_ids
        if invalid_ids:
            raise ValueError("error_player_not_in_club")

        existing_stats = session.scalars(
            select(PlayerStats).where(PlayerStats.player_id.in_(player_ids))
        ).all()
        existing_player_ids = {s.player_id for s in existing_stats}

        for pid in player_ids:
            if pid not in existing_player_ids:
                new_stat = PlayerStats(player_id=pid)
                session.add(new_stat)
        session.flush()

        stat_column = VALID_STATS[stat]
        session.execute(
            update(PlayerStats)
            .where(PlayerStats.player_id.in_(player_ids))
            .values({stat_column: stat_column + 1})
        )
        session.commit()
        return len(player_ids)