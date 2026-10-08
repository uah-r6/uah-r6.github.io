# UAH R6 branding

Verified 2026-10-07 against the [current official UAH brand guide](https://www.uah.edu/omc/resources/brand) (2025–present).

| Role | Official screen value |
| --- | --- |
| Primary blue | `#0058A4` |
| Navy | `#002D72` |
| Small yellow accents | `#FDDA24` |
| Black | `#2C2A29` |

The guide recommends Red Hat Text. The website uses its publicly available Google Fonts distribution, with Arial/sans-serif fallbacks. No proprietary font files are bundled. Yellow is reserved for small details rather than large background areas.

## Esports asset

The unmodified 1080 × 1080 PNG in `web/public/brand/uah-esports-logo.png` was downloaded from the **Site home image on the official [UAH Esports website](https://esports.uah.edu/)** on 2026-10-07. It is the stylized Charger mark used on that Esports site and in its team photographs; it was not sourced from Athletics or a fan copy. The official site serves the asset through Google Sites' `lh7-us.googleusercontent.com/sitesv-images-rt/` CDN, whose signed image URLs change between page loads. The permanent source is the official homepage.

The file remains in its original PNG format, with its original transparency and artwork. Components reference one replaceable file and use `object-fit: contain`; a later official SVG or different-resolution PNG needs no layout redesign.

## Team accents

Blue initially uses official primary blue. White initially uses `#E6EDF5`. Administrators can edit any team's six-digit hex color. `web/src/theme.ts` derives readable accents against the dark card background and chooses a contrasting foreground. Names, scope labels, and status text communicate meaning independently of color. Team names never select special theme code.

## Team logos

The four user-supplied `UAH_Logo_Blue/White/Grey/Black.png` assets are copied **byte
for byte** to `web/public/brand/teams/{blue,white,grey,black}.png`. Each is a valid
1080 x 1080 RGBA PNG with transparency, between 64 and 95 KiB. Artwork, canvas,
proportions and alpha are preserved; no cropping, recoloring or regeneration.
The existing program mark above remains in public navigation and local admin
branding.

`web/src/teamLogos.ts` is the single public presentation registry keyed by normal
team slug. `TeamLogo.tsx` handles sizing and failure: known slug asset, then the
program logo, then a plain UAH mark if both images fail. Unknown teams go directly
to the program logo. No filesystem paths or logo metadata enter exported JSON.
Grey and Black are ready for future normal team records; installing an asset
does not create, activate or expose a team in navigation.

To add a future logo, put its approved unchanged PNG in `brand/teams/`, add one
slug/path entry to the registry and an asset/mapping test. No page-specific
mapping is needed. All callers use team identity from existing metadata.
The public component respects Vite's base path; admin passes `/` because FastAPI
serves shared brand assets at `/brand/`, outside its `/admin/` application base.

One logo identifies each team header (including roster), selected Player Stats,
owning series and match. Program team cards and local team editors also use it.
Native selectors stay text-based; compact context logos accompany admin selection
and Google Sites embeds (a 32px row plus 6px spacing). Public player heroes use
their scoped regular team contributions for identity; multi-team views use the
program mark. Individual player rows do not repeat team logos. See
[Public presentation](PUBLIC_PRESENTATION.md) for the larger public identity
heroes and cards; compact embeds and local admin retain their utility sizing.

The shared neutral CSS chip supports light and dark artwork without modifying
the images. Images use `object-fit: contain`, fixed responsive bounds and no
color filters. Adjacent team names carry identity; those logos have empty alt
text. Standalone use has a team-name alt label.

Verification: `cd web; npm.cmd test`, both builds, then run the real quoted
`& '.\Start NECC Admin.cmd'` from the repository root and
`.\.venv\Scripts\python.exe scripts/verify-team-logos-ui.py`. The browser script
checks current pages at 1440/1100/768/390px, future-team fixtures, missing images,
embed links, selectors, transparency and read-only admin previews. For deployed
Pages, pass `--url https://uah-r6.github.io/ --output <ignored-output-directory>`.
`scripts/verify-team-branding-preservation.py` checks the private pre-pass backup
against SQLite, public JSON, archives and protected source hashes.
