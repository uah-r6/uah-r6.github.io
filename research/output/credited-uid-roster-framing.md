# Consumed UID list framing — 2026-10-03

Explicit framing discovery in the two previously sealed buffers, not a damage/DBNO/downer decoder.

| Buffer | Complete ten-entry lists | Literal UID occurrences covered | Unclassified remaining | Distinct UID orders |
| --- | ---: | ---: | ---: | ---: |
| 8580 R06 | 237 | 2370 | 5697 | 1 |
| 8583 R02 | 289 | 2890 | 6373 | 1 |

Observed local framing: byte0x0a followed by10entries, each8-byte little-endian known UID plus exactly3opaque bytes (`20 00 ff` or `21 00 ff`), total111bytes. Accept only all10distinct expected header UIDs; reject duplicates, unknown replacement, wrong count, width/suffix, truncation and overlap. Array order is not an ownership rule. This recognizes a raw counted list; its outer network packet/type and suffix semantics remain undecoded.

526lists/5260literal UID matches are now framed.12070other occurrences remain unclassified, besides20known UID property records. Repeated full roster lists occur as ordinary same-round controls; none of these exact fixed-width lists appears within±50000bytes of the independently reviewed DBNO/credit/final-death/finish anchors. The window is a byte-context control, never a time interval or proof of absence elsewhere. A fuller variable-width structure remains a separate lead.

No directed attacker/victim field, HP/life-state meaning, downer or event timestamp is established by this list. Do not assign from nearby references or count. All decoded raw offsets/lists and opaque suffix distributions stay private. No old discovery result overwritten, parser/default change, historical migration or target/evaluation repeated.
