# portpulse

tired of `Error: listen EADDRINUSE: address already in use :::3000`? yeah me too.

interactive terminal tool to see what ghost process is hogging your ports and kill it instantly with one key.

## what it does

- scans all active listening ports (tcp/udp) and maps them to real process names & pids
- interactive tui: arrow keys to move, `k` to kill, `K` to nukes the whole process tree, `/` to filter
- scriptable cli: `portpulse kill 3000` or `portpulse find 8080`
- zero external bloat, cross-platform (windows, macos, linux)

## install

```bash
pip install portpulse
```

or run without installing:
```bash
pipx run portpulse
```

## usage

### interactive mode (tui)
just run:
```bash
portpulse
```
or if your python scripts folder isn't in PATH:
```bash
python -m portpulse
```

controls:
- `↑ / ↓` or `j / k`: navigate
- `k`: kill selected process
- `K`: force kill process tree (children included)
- `/`: search / filter by port number or process name
- `r`: refresh list
- `q` / `esc`: quit

### cli mode

```bash
# see everything running
portpulse list

# check a specific port
portpulse find 3000

# free port 3000 right now
portpulse kill 3000

# free multiple ports at once
portpulse kill 3000 8080 5432

# dump as json for scripts
portpulse list --json
```

## development

```bash
git clone https://github.com/emirplus/portpulse
cd portpulse
pip install -e .
python -m unittest discover tests
```

## license

MIT
