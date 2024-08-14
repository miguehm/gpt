# Terminal GPT

A CLI tool send prompts to chatgpt

## TODO

- [ ] Support Gemini?
- [x] Data App
  - [x] Config file
  - [x] Session database file
- [ ] Config menu.
  - [x] Config show.
  - [ ] Modify using flag?
- [ ] `--hot` to quick responses (Toggle between 4o and 4o-mini).
- [ ] Multiple chats.
  - [x] Show history.
  - [x] Send chat history for more context.
  - [x] Delete chats via `gpt delete`.
  - [ ] Modify chat title?
- [ ] Sessions Selector.
  - [x] Selection using UP/DOWN keys.
  - [ ] Paginate selection list using LEFT/RIGHT keys.
- [x] Log mode
  - [x] Toogle log mode

## Installation

> Installation via to PyPi soon.

### Using wheel file

- Download the latest version from [releases](https://github.com/miguehm/gpt/releases).

```bash
pip install gpt-0.4-py3-none-any.whl
```

## Auth to OpenAI

Add to .bashrc file

```bash
export OPENAI_API_KEY="your_secret_key"
```

Update session

```bash
source .bashrc
```
