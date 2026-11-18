# The hub starts and stops with hub.py

Status: accepted 2026-11-18 · #154

## Context

docs-site 0.3.0's `hub.py` has `install`, `update`, `status` and `remove`. Stopping and starting the hub takes `docker compose -p docs-site stop` and `start`, which the README lists (#153) and the `/docs-site:hub` skill doesn't. Three things go wrong with that, each checked on the author's machine on 2026-11-18:

- `/docs-site:init` starts a stopped hub. It runs `hub.py update`, which runs `docker compose up -d`. With all four containers stopped, `hub.py update --repo ~/Projects/astrocode` started all four.
- `status` misreads a stopped site. It prints `container exited, not answering (502)`, and the skill says `container exited` means the repo's folder is gone and to run `install`.
- `hub.py` is at a path with the plugin's version in it, `~/.claude/plugins/cache/astro-plugins/docs-site/VERSION/scripts/hub.py`, so it's hard to run by hand.

## Decision

`hub.py` gets `start` and `stop`, and only `install`, `start`, `stop` and `remove` change whether the hub runs:

```
hub.py install [--port N]   # create the hub, or bring it up to date, and start it (unchanged)
hub.py start                # start the hub; refuses when none is installed
hub.py stop                 # stop the dashboard and every site
hub.py status               # a stopped hub or site says "stopped"
hub.py remove               # stop the hub, and remove its containers and folder (unchanged)
hub.py update [--repo DIR]  # what /docs-site:init runs; leaves a stopped hub stopped
```

- `start` does what `install` does on an installed hub: it writes the hub's files from the repos on record, runs `docker compose up -d --remove-orphans`, and waits for each site to answer. So it also recreates removed containers, adds repos set up since, and drops repos whose folder is gone. When no hub is installed, it says so and runs nothing, so a mistaken `start` never downloads the two images (about 360 MB) or creates a hub.
- `stop` runs `docker compose stop`. The containers have `restart: unless-stopped`, so Docker keeps them stopped through a reboot until `start`. On 2026-11-18 a stopped site stayed `exited` through `systemctl restart docker` while the other three came back.
- The hub counts as stopped when its proxy container isn't running. Docker's own state says so, and no file records it.
- `update` on a stopped hub writes the files and runs `docker compose up --no-start --remove-orphans`, which creates a new repo's container and starts nothing. Tested on a scratch Compose project: a stopped container stayed `exited` and a new one was `created`. `/docs-site:init` then says the hub is stopped and that `/docs-site:hub start` serves the new site.
- `status` says `stopped` for a site whose container is `exited` or `created`, and `no container` for one that's missing, each with the command that fixes it. A site whose folder is gone isn't listed at all, because the hub's list of sites skips it. `status` still exits 1 when anything doesn't answer.
- The skill takes a command as its argument, such as `/docs-site:hub stop`, with `argument-hint: [install|start|stop|status|remove]`. With no argument it installs or checks the hub as it does now. It runs `stop` and `remove` only when the user asks.
- The skill pre-approves `status`, `start` and `stop`. `start` and `stop` change nothing a second `start` or `stop` can't undo. `install` and `remove` still ask, since the first downloads images and the second deletes the hub's folder.
- The README's "Use the hub" section uses `/docs-site:hub start` and `stop`, and `hub.py start` and `stop`. It keeps `docker compose -p docs-site stop site-NAME` for one site, and says that such a site starts again at the next `install`, `start` or `/docs-site:init`.

## Turned down

- `start` as `docker compose start`. It starts only containers that exist, so after `docker compose down` or `docker container prune` it does nothing, and it doesn't add or drop repos.
- A file that records whether the hub is stopped. Docker already keeps that state through reboots, and a file could disagree with it.
- `start NAME` and `stop NAME` for one site. Docker Compose does it in one command, and keeping one site stopped through `update` needs a record of which sites are stopped.
- A `down` command that removes the containers and keeps the files. `stop` pauses the hub and `remove` tears it down, and `down` would save only the containers' disk space.
- A launcher in `~/.local/bin` for the versioned path. `/docs-site:hub stop` gives a fixed name without writing files outside the data folder.

## Consequences

- docs-site 0.4.0, with tests for each new path through FakeDocker: `start` with and without a hub, `stop`, `update` on a stopped hub, and `status` on stopped and missing containers.
- A repo set up while the hub is stopped isn't served until `start`.
- A site stopped with `docker compose -p docs-site stop site-NAME` starts again on the next `install`, `start` or `update`.
