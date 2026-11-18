---
name: hub
description: Serve every project's docs at once behind one address, with a dashboard that lists them - each site at http://NAME.localhost:8099 and the dashboard at http://localhost:8099, in Docker containers that start at boot and reload a page when it changes. Use when the user asks for a docs hub or dashboard, to see every project's docs in one place, to keep docs sites running, or why a docs site at a .localhost address isn't answering.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hub.py status)
---

# Serve every project's docs

The hub is a Docker Compose project, `docs-site`, that serves the docs of every repo `/docs-site:init` has set up:

- `http://localhost:8099` is the dashboard. It lists each project's address, a line about it and its repository.
- `http://NAME.localhost:8099` is a project's site. NAME is the repo's folder name in lowercase, with anything but letters and digits turned into hyphens. A second repo with the same folder name gets `NAME-2`. Browsers and this machine's resolver send every `.localhost` name to this machine, so the names need no setup.
- Each site is a container that runs `zensical serve` in its repo, so a changed page is rebuilt and reloads in the browser. One Caddy container routes the names to them. It's the only one with a host port, so `uvx zensical serve` in a repo still works while the hub runs.
- The containers restart if they exit, and start with Docker at boot.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hub.py install    # write the hub's files and start it
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hub.py status     # whether the dashboard and each site answer
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hub.py remove     # stop the hub, and remove its containers and folder
```

`install` and `remove` start and stop containers, so only `status` is pre-approved. The hub's files are in `~/.local/share/docs-site/hub/`: `compose.yml`, the proxy's `caddy/Caddyfile` and the dashboard, `www/index.html`. `install` writes all three from the repos on record, so an edit to one is overwritten.

## Install it

Run `install`. It needs Docker with its compose plugin, and the first run downloads two images, `zensical/zensical` and `caddy:2-alpine`, about 360 MB together. Pass `--port N` for a port other than 8099; later runs keep it.

It prints which of its files it created, updated or kept, then the dashboard's address and each site's. Running it again is safe: it starts only what isn't running and changes only what's out of date. Once a hub is installed, `/docs-site:init` adds a new repo to it without this skill.

Tell the user the dashboard's address and each site's.

## A site that isn't answering

`install` marks a site `not answering yet`, and `status` says `not answering`, with the container's state. `status` exits 1 when anything isn't answering.

- `container restarting`: `zensical serve` keeps exiting. The usual cause is that the branch checked out in that repo has no `mkdocs.yml`. The site comes back by itself, within about a minute, once the file does.
- `container running` but not answering: the first build is still running, or a page failed to build.
- `container exited`: the repo's folder is gone, so Docker can't start the site. Run `install` again, which drops a repo whose folder is gone. The hub's mounts never create a missing folder: Docker would make it as root where the repo was.

In each case, read the site's log and show the user what it says:

```
docker compose -p docs-site logs site-NAME
```

The site's own address says the same when it's down: "The docs site for NAME is not running", with that command.

## Update Zensical

The sites run the Zensical in the image, which changes only when the image is downloaded again:

```
docker compose -f ~/.local/share/docs-site/hub/compose.yml pull
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hub.py install
```

The proxy sends each request to Zensical's server with `Host` and `Origin` set to `localhost`, because that server answers 400 otherwise. If pages stop reloading on a change after an update, check that first: `status` still passes, since the pages themselves are served.
