# GeoLite2-Country Database

This database (`GeoLite2-Country.mmdb`) is used to detect a visitor's country
from their IP address, so the site can automatically show Bengali to visitors
in Bangladesh and English to everyone else on their first visit.

**Source & Attribution:** This product includes GeoLite2 data created by
MaxMind, available from https://www.maxmind.com. Mirrored (auto-updated) via
https://github.com/wp-statistics/GeoLite2-Country under the CC BY-SA 4.0
license.

**Keeping it up to date:** IP-to-country mappings drift slowly over time as
ISPs get reassigned address blocks. For a small charity site this drift is
minor and not worth worrying about day-to-day, but every 6–12 months it's
worth re-downloading the latest `GeoLite2-Country.mmdb.gz` from the link
above, decompressing it, and replacing this file.

**If this file is ever missing or fails to load**, the site does not break —
`config/middleware.py` catches that case and simply defaults everyone to
Bengali (today's current behavior), same as if this feature didn't exist.
