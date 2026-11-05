"""Reversible series counting policy; recorded performance stays intact."""


def counted(matches):
    return [match for match in matches if not match.get('exclude_from_stats', False)]
