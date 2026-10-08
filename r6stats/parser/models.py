from dataclasses import asdict, dataclass, field


@dataclass
class Player:
    profile_id: str
    username: str
    team: int
    operator: str = "Unknown"
    side: str = "Unknown"

    @property
    def key(self) -> str:
        # LAN professional replays can report the nil UUID for every player.
        # It is not a usable identity; match feedback still carries usernames.
        return (self.profile_id if self.profile_id and
                self.profile_id != "00000000-0000-0000-0000-000000000000"
                else self.username.strip().casefold())


@dataclass
class Kill:
    sequence: int
    remaining: float
    killer: str
    victim: str
    killer_team: int
    victim_team: int
    headshot: bool = False

    @property
    def teamkill(self) -> bool:
        return self.killer_team == self.victim_team


@dataclass
class Objective:
    kind: str
    player: str
    team: int
    remaining: float


@dataclass
class ObjectiveOccurrence:
    """Round-level evidence; separate from player-credited Objective rows."""
    kind: str
    source: str
    plant_state_offset: int
    actor: str | None = None
    actor_uid: int | None = None
    actor_source: str | None = None
    actor_reason: str | None = None
    actor_evidence: dict | None = None


@dataclass
class Round:
    number: int
    site: str
    winner: int
    win_condition: str
    players: list[Player] = field(default_factory=list)
    kills: list[Kill] = field(default_factory=list)
    objectives: list[Objective] = field(default_factory=list)
    starting_scores: tuple[int, int] | None = None
    ending_scores: tuple[int, int] | None = None
    objective_occurrences: list[ObjectiveOccurrence] = field(default_factory=list)


@dataclass
class Match:
    replay_id: str
    timestamp: str
    map_name: str
    match_type: str
    game_mode: str
    rounds: list[Round]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict) -> "Match":
        rounds = []
        for row in value["rounds"]:
            rounds.append(Round(row["number"], row["site"], row["winner"], row["win_condition"],
                                [Player(**p) for p in row["players"]],
                                [Kill(**k) for k in row["kills"]],
                                [Objective(**o) for o in row["objectives"]],
                                tuple(row["starting_scores"]) if row.get("starting_scores") is not None else None,
                                tuple(row["ending_scores"]) if row.get("ending_scores") is not None else None,
                                [ObjectiveOccurrence(**o) for o in row.get("objective_occurrences", [])]))
        return cls(value["replay_id"], value["timestamp"], value["map_name"],
                   value["match_type"], value["game_mode"], rounds)
