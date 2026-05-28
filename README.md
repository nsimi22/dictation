# free-dictation

A **free, local, privacy-first dictation app** for macOS and Windows — a free
alternative to [Willow Voice](https://willowvoice.com/).

**Hold a key, speak, release** — and your words are transcribed and typed
straight into whatever app has focus (your editor, browser, Slack, anywhere).
Transcription runs entirely on your machine with
[faster-whisper](https://github.com/SYSTRAN/faster-whisper), so it's **100%
free, works offline, and your audio never leaves your computer**.

```
   ┌──────────┐   hold hotkey    ┌───────────┐   release   ┌─────────────────┐   types text
   │   you    │ ───────────────▶ │  record   │ ──────────▶ │ Whisper (local) │ ──────────▶ focused app
   └──────────┘   & speak        └───────────┘             └─────────────────┘
```

## Features

- 🎙️ **Hold-to-talk**: hold a hotkey while you speak, release to insert text.
- 🔒 **Local & private**: audio is transcribed on-device; nothing is uploaded.
- 💸 **Free**: no subscription, no API keys, no usage limits.
- ⌨️ **Types anywhere**: pastes into the focused app (or types key-by-key).
- 🖥️ **Desktop app**: a simple window to configure settings and start/stop.
- 🖥️ **Cross-platform**: macOS and Windows from a single codebase.
- ⚙️ **Configurable**: model size, hotkey, language, output mode, and more.

## Requirements

- **Python 3.9+**
- A working **microphone**
- A few hundred MB of disk for the Whisper model (downloaded automatically on
  first run)

## Install (recommended — for everyday users / your team)

The easiest way to get `dictate` and `dictate-gui` onto your machine is one
command. It uses [pipx](https://pipx.pypa.io/) to install the app in its own
isolated environment and put the commands on your PATH. **Requires Python 3.9+.**

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/nsimi22/dictation/main/scripts/install.sh | bash
```

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/nsimi22/dictation/main/scripts/install.ps1 | iex
```

Then open a new terminal and run **`dictate-gui`** (or `dictate`).

Prefer to do it by hand? It's just pipx:

```bash
python3 -m pip install --user pipx        # if you don't have pipx yet
pipx install git+https://github.com/nsimi22/dictation.git
```

To **update** later, re-run the install command (or `pipx reinstall free-dictation`).

> **Private repo?** If the GitHub repo isn't public, your teammates need read
> access to it. Use the SSH URL so git auth just works:
> `DICTATION_REPO=git@github.com:nsimi22/dictation.git` before running the
> script (or `pipx install "git+ssh://git@github.com/nsimi22/dictation.git"`).

> **macOS note:** if you hit a `PortAudioError`, install PortAudio once with
> `brew install portaudio`, then re-run the installer.

## Install from source (for development)

```bash
git clone https://github.com/nsimi22/dictation.git
cd dictation
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .                 # gives you the `dictate` command
```

## Desktop app (GUI)

Prefer a window over the terminal? Launch the desktop app:

```bash
dictate-gui          # or:  dictate --gui
```

It gives you a simple window to:

- pick your **hotkey, model, language, microphone, and output mode** and **Save**
  them (writes the same config file as below);
- **Start / Stop** dictation with a button;
- watch a live **status** light (ready → recording → transcribing) and a log of
  everything you've dictated.

The GUI uses Tkinter, which is bundled with the official python.org installers
on macOS and Windows — nothing extra to install. (If you built Python yourself
and Tkinter is missing: macOS `brew install python-tk`; otherwise just use the
`dictate` CLI below.)

## Run (command line)

```bash
dictate
```

You'll see something like:

```
Loading Whisper model 'base.en' (cpu/int8)...
Ready. Hold [right_cmd] and speak; release to dictate. Press Ctrl+C to quit.
```

Now hold the hotkey (**right ⌘ Command** on macOS by default), say a sentence,
and release. The text appears wherever your cursor is.

Quit with `Ctrl+C` in the terminal.

> Don't want to install the package? You can also run it directly with
> `PYTHONPATH=src python -m dictation` from the repo root.

## macOS permissions (important!)

macOS requires explicit permission for an app to listen to the keyboard and
type into other apps. The **first time** you run `dictate`, macOS will prompt
you — or you may need to grant these manually in
**System Settings → Privacy & Security**:

1. **Accessibility** — required to detect the global hotkey and to type/paste
   into other apps. Add your terminal (Terminal.app / iTerm) **or** your Python
   binary and enable it.
2. **Microphone** — required to record audio. Allow it for your terminal.
3. **Input Monitoring** — on some macOS versions this is also needed for the
   global hotkey listener.

After granting permission you may need to **restart your terminal**. If text
isn't being typed, this is almost always the cause.

## Configuration

Generate a config file you can edit:

```bash
dictate --init
```

This writes `config.yaml` to:

- **macOS:** `~/Library/Application Support/free-dictation/config.yaml`
- **Windows:** `%APPDATA%\free-dictation\config.yaml`

See [`config.example.yaml`](config.example.yaml) for every option with comments.
Key settings:

| Setting        | Default (macOS) | Notes                                                        |
|----------------|-----------------|--------------------------------------------------------------|
| `hotkey`       | `right_cmd`     | Hold-to-talk key. `dictate --list-keys` lists valid names.   |
| `model`        | `base.en`       | `tiny`/`base`/`small`/`medium`/`large-v3` (+ `.en` variants).|
| `language`     | `en`            | Language hint; set to `null` to auto-detect.                 |
| `output_mode`  | `paste`         | `paste` (Cmd/Ctrl+V) or `type` (per-keystroke).              |
| `min_duration` | `0.3`           | Ignore taps shorter than this (seconds).                     |

You can also override common settings per run:

```bash
dictate --model small.en --hotkey right_option --language auto
```

### Choosing a model

| Model        | Speed   | Accuracy | Notes                          |
|--------------|---------|----------|--------------------------------|
| `tiny.en`    | fastest | ★★       | Great on slow CPUs.            |
| `base.en`    | fast    | ★★★      | **Default** — good balance.    |
| `small.en`   | medium  | ★★★★     | Noticeably better English.     |
| `medium.en`  | slow    | ★★★★★    | Slow on CPU; great with a GPU. |
| `large-v3`   | slowest | ★★★★★    | Best quality; needs a GPU.     |

If you have an NVIDIA GPU, set `device: cuda` for a big speedup.

## Useful commands

```bash
dictate --list-keys       # show accepted hotkey names
dictate --list-devices    # list microphones (pick an index for input_device)
dictate --init            # write a default config file
dictate --version
```

## Troubleshooting

- **No text appears (macOS):** grant **Accessibility** + **Input Monitoring**
  permission and restart your terminal (see above).
- **`PortAudioError`:** `brew install portaudio` (macOS) and reinstall
  `sounddevice`.
- **First run hangs / downloads:** the Whisper model is downloading; subsequent
  runs are instant.
- **Transcripts are wrong/garbled:** try a bigger `model` (e.g. `small.en`) and
  make sure the right microphone is selected via `--list-devices` /
  `input_device`.
- **Pasting overwrites my clipboard:** it's restored automatically; if you use
  `output_mode: type` instead, the clipboard is never touched.

## How it works

| Module                      | Responsibility                                   |
|-----------------------------|--------------------------------------------------|
| `dictation/app.py`          | Orchestrates hotkey → record → transcribe → type |
| `dictation/gui.py`          | Tkinter desktop app for settings + start/stop    |
| `dictation/audio.py`        | Microphone capture (`sounddevice`)               |
| `dictation/transcribe.py`   | Local speech-to-text (`faster-whisper`)          |
| `dictation/output.py`       | Pastes/types text into the focused app           |
| `dictation/keys.py`         | Friendly hotkey-name parsing (`pynput`)          |
| `dictation/text.py`         | Transcript cleanup/formatting                    |
| `dictation/config.py`       | YAML config + defaults                           |

## Development

```bash
pip install -r requirements.txt
pip install pytest
PYTHONPATH=src python -m pytest -q
```

The `text` and `config` modules are covered by tests that run without any
audio hardware or model downloads.

## License

MIT — see [LICENSE](LICENSE).
