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
