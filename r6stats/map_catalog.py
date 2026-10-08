"""Public replay-map identities, maintained from siege-dissect's Map enum.

This includes legacy replay maps, not a claim about today's competitive pool.
Aliases only normalize presentation/aggregation; replay parsing is unchanged.
"""
import hashlib
import re

from r6stats.parser.siege_dissect import MAP_LABELS, map_label

# (native enum name, public canonical name). Version variants share an identity.
SUPPORTED_MAPS = (
    ('ClubHouse', 'Clubhouse'), ('KafeDostoyevsky', 'Kafe Dostoyevsky'),
    ('Kanal', 'Kanal'), ('Yacht', 'Yacht'), ('PresidentialPlane', 'Presidential Plane'),
    ('Consulate', 'Consulate'), ('BartlettU', 'Bartlett University'),
    ('Coastline', 'Coastline'), ('Tower', 'Tower'), ('Villa', 'Villa'),
    ('Fortress', 'Fortress'), ('HerefordBase', 'Hereford Base'),
    ('ThemePark', 'Theme Park'), ('Oregon', 'Oregon'), ('House', 'House'),
    ('Chalet', 'Chalet'), ('StadiumBravo', 'Stadium Bravo'),
    ('Skyscraper', 'Skyscraper'), ('Border', 'Border'), ('Favela', 'Favela'),
    ('Bank', 'Bank'), ('Outback', 'Outback'), ('EmeraldPlains', 'Emerald Plains'),
    ('NighthavenLabs', 'Nighthaven Labs'), ('Lair', 'Lair'), ('Stadium2020', 'Stadium 2020'),
)


def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


CATALOG = tuple({'slug': slug(name), 'name': name, 'supported': True}
                for _, name in SUPPORTED_MAPS)
_ALIASES = {alias.casefold(): name for native, name in SUPPORTED_MAPS
            for alias in (native, name)}
_ALIASES['consulatey7'] = 'Consulate'
_ALIASES.update({alias.casefold(): name for alias, name in MAP_LABELS.items()})


def identity(value):
    raw = map_label(value)
    canonical = _ALIASES.get(raw.casefold())
    if canonical:
        return {'slug': slug(canonical), 'name': canonical, 'supported': True}
    # Preserve unfamiliar recorded labels without guessing their map identity.
    digest = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]
    return {'slug': 'unrecognized-' + digest, 'name': raw or 'Unknown map', 'supported': False}
