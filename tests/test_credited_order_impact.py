"""Hypothetical event-count auditing must never calculate revised Ratings."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research'))
from credited_uah_order_impact import count_calculator
from r6stats.parser.models import Kill, Match, Player, Round
import r6stats.stats.calculate as engine


def test_order_audit_isolates_globals_and_suppresses_both_rating_formulas(monkeypatch):
    def forbidden(*_):
        raise AssertionError('Audit computed Rating from changed inputs')

    monkeypatch.setattr(engine, 'calculate_rating', forbidden)
    original_chronological = engine.chronological
    original_finalize = engine.finalize
    participants = [Player('a', 'a', 0, side='Attack'), Player('aa', 'aa', 0, side='Attack'),
                    Player('b', 'b', 1, side='Defense'), Player('bb', 'bb', 1, side='Defense')]
    # Independent HUD controls establish this type of clock-reset reversal.
    round_ = Round(1, 'site', 0, 'win', players=participants,
                   kills=[Kill(0, 6, 'a', 'b', 0, 1), Kill(1, 42, 'bb', 'a', 1, 0)])
    match = Match('id', 'date', 'Bank', 'Custom Game', 'Bomb', [round_])
    for version in ('siege_style_v2', 'collegiate_v1'):
        old = count_calculator(packet_order=False)(match, rating_version=version)
        packet = count_calculator(packet_order=True)(match, rating_version=version)
        assert old['bb']['opening_kills'] == 1
        assert packet['a']['opening_kills'] == 1
        assert all(row['rating'] is None for row in (*old.values(), *packet.values()))
        assert old['a']['kills'] == packet['a']['kills'] == 1
    assert engine.chronological is original_chronological
    assert engine.finalize is original_finalize
    assert engine.calculate_rating is forbidden
