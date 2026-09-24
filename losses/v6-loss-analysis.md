# v6 loss replay audit

Audited 153 replay files for the active C++ v6 submission (submission 1776). Each replay was decoded for the match outcome, ending round, deciding tiebreak, and the final own-dragon death category. Replay observations are not a substitute for the opponent's source code, and the last death in a match is not necessarily its strategic root cause.

## Overall outcome

| Result | Games |
| --- | ---: |
| Team eliminated | 62 |
| Reached round limit | 91 |
| Round-limit loss on longest dragon | 82 |
| Round-limit loss on total team length | 9 |

The primary systematic weakness is the late-game flagship/longest-dragon tiebreak: it decided 82 of 91 round-limit losses. The 62 elimination losses form a separate survival problem, strongest on cramped maps.

## Map patterns

Map names below come from each replay itself (the API manifest's map field is series-level, so it must not be used as a per-game map label).

| Map | Losses | Eliminated | Round limit | Longest dragon | Total length | Other signal |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Arena (11×11) | 7 | 7 | 0 | 0 | 0 | Average ending round 92.6; median peak population 6 |
| Colloseum (16×16) | 7 | 7 | 0 | 0 | 0 | Early survival failures |
| Default (32×32) | 19 | 5 | 14 | 14 | 0 | Tiebreak losses all on longest dragon |
| Default Small (16×16) | 23 | 20 | 3 | 3 | 0 | Most losses are elimination |
| Queen Of Spades (25×35) | 18 | 3 | 15 | 12 | 3 | Mostly tiebreak losses |
| Schooltime (60×40) | 20 | 5 | 15 | 14 | 1 | Mostly tiebreak losses; median peak population 16 |
| Trophy (25×25) | 23 | 11 | 12 | 10 | 2 | Mixed survival and tiebreak failures |
| Big Empty (64×64) | 12 | 0 | 12 | 11 | 1 | Median peak population 60; no wall deaths in the final-death sample |
| Devil (32×16) | 10 | 4 | 6 | 5 | 1 | Mixed |
| Internal testing map (64×64) | 3 | 0 | 3 | 3 | 0 | All tiebreak losses |
| stronghold (48×24) | 2 | 0 | 2 | 2 | 0 | All tiebreak losses |
| Trauma (48×24) | 9 | 0 | 9 | 8 | 1 | All reached round limit |

## Final-death categories

| Final own-dragon death | Games |
| --- | ---: |
| Wall / kelp | 51 |
| Self-collision | 46 |
| Head-to-head | 30 |
| Other dragon body | 26 |

These categories sum to one final death per replay. They describe how the last recorded own dragon died, not whether that death caused the match loss. In particular, a late death can occur after the tiebreak was already effectively lost.

## Evidence-backed C++ changes

`cpp_bot/main.cpp` now protects the designated flagships from recurring risks:

- On maps larger than 12×12, designated flagships stop splitting at length 8, and any flagship stops splitting once the map's collector population target is reached. The threshold is a compromise: length 4 protected the biggest boards but regressed the broader comparison; length 16 waits too long to protect growth. Small Arena-sized maps still prioritize building the early collector group.
- Move scoring no longer lets a large-map flagship take a pearl shortcut into a zero-mobility pocket, and its reachable-area requirement is based on its length. Arena-sized maps retain a small, bounded pearl-pocket exception because all seven Arena losses were early eliminations and the median peak population was only six.
- Anti-loop history now retains at least the current body length (or 256 positions, whichever is larger), instead of always discarding everything older than 256 moves. This closes a blind spot for dragons longer than 256 segments; it is a code-level safety correction, not yet an independently proven win-rate improvement.
- Boards with at least 3,000 tiles now target 40 dragons instead of 60. This keeps the count within the earlier 30–60 target while addressing the 64×64 map's 60-dragon peak and repeated longest-dragon losses; the lower cap is limited to very large boards so Schooltime and medium maps keep their previous target.

## Verification and limits

The exact current C++ bot compiled and completed local matches. With the 40-dragon cap, a clean, side-swapped 10-game comparison against the untouched v6 baseline across Arena, Default Small, Default, Big Empty, and Schooltime finished 7–3 for the revised version, with no errors or draws. Side-swapped map pairs: revised wins both orientations on Default Small and Schooltime; the other three maps split one win each by side. A separate 10-game Big Empty check finished 5–5, but Team A won all ten, so that batch is dominated by starting-side advantage and does not establish a bot-specific win. The Big Empty weakness is reduced in the paired result but is not solved.

The largest-map C++ build also completed in the judge-style sandbox; the observed peak was 4.5 million CPU points per turn against the 100 million limit.

The changes directly target the strongest replay-wide signal (longest-dragon tiebreak losses) and preserve early population growth on small maps. They do not establish that every historical loss would now be won. The elimination cases still need more targeted work—especially Arena/Default Small—and Big Empty needs more tests with randomized starting side. The opponent source/binaries for historical games are not included in the replays, and a final death category alone cannot be treated as a unique strategic cause; exact per-game certainty is therefore not possible from replay evidence alone.
