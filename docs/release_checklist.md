# Release Checklist

Run for every release, alongside docs/release-plan.md. Phase 4 of the
release plan executes this list.

## Code

- [ ] Full pytest suite green (`python -m pytest`)
- [ ] No TODO comments in shipped files
- [ ] No debug print statements (windowed builds have no stdout)
- [ ] No unused imports
- [ ] `grep` for em dashes in shipped files comes back empty

## UI

- [ ] All six condition themes verified (clear, cloudy, rain, snow,
      mist, night)
- [ ] Condition menu pin and Auto both work
- [ ] Hourly strip, forecast range bars, and favorites render
- [ ] Unit toggle flips every panel
- [ ] Window centers on first show; saved geometry restores
- [ ] 150 percent display scaling looks sharp (High DPI attributes on)

## Behavior

- [ ] Current weather search works
- [ ] Autocomplete popup appears and is styled dark glass
- [ ] Bad city shows the hand-written 404 message, no technical text
- [ ] No internet shows the network message and the saved-weather note
- [ ] Auto refresh repeats the last city quietly
- [ ] Offline start shows the cached weather with its timestamp

## Secrets

- [ ] `git ls-files` shows no `.env`, no logs/, no cache.json,
      settings.json, favorites.json
- [ ] Dist tree scan (release-plan item 0.2) found no key material
- [ ] Log file reviewed: URLs redacted to `appid=***`

## Packaging

- [ ] VERSION bumped, changelog entry written
- [ ] `build.ps1` ran clean: tests, icon, PyInstaller, secret scan, zip
- [ ] Built EXE: window icon and file-properties version correct
- [ ] EXE smoke test passed (search, conditions, error path)
- [ ] Installer installs and uninstalls cleanly
- [ ] Portable zip runs without admin rights
- [ ] Data files land in the app data directory, not next to the EXE

## Documentation

- [ ] README install section current (installer, portable, source)
- [ ] Public screenshots under docs/screenshots/ refreshed
- [ ] agent.md architecture tree matches disk
- [ ] GitHub release tagged with installer, zip, and checksums
