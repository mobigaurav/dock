# How to publish Dock (`dock-inbox`)

Product and CLI: **Dock**. PyPI name: **`dock-inbox`**. Import package: `dock`.

`pip install dock` must never be the instruction — that name is a molecule-docking toolkit.

## First release (v0.1.0)

1. Merge this work to `main` and `git tag v0.1.0 && git push origin main --tags`.
2. Create a GitHub Release from that tag.
3. PyPI trusted publishing (preferred) or a one-time token:
   - [pypi.org/manage/account](https://pypi.org/manage/account/) → API token, or GitHub Actions trusted publisher for `mobigaurav/dock`.
   - Build: `python -m pip install build twine && python -m build`
   - Upload: `twine upload dist/*` (or the official `pypa/gh-action-pypi-publish` workflow).
4. Verify: `pip install dock-inbox==0.1.0 && dock --help`
5. Point Arogya’s `.github/workflows/dock.yml` at `pip install dock-inbox==0.1.0` instead of `git+https`.

## What other developers run

```bash
pip install dock-inbox
```

Copy `examples/github-inbox.yml` to `.github/workflows/dock.yml`. They need `gh` locally for `dock merge --pr`; GitHub Actions uses `GITHUB_TOKEN`.

## Do not

- Upload as `dock` or `agentdock` (taken).
- Pin CI to `@main`.
- Promise an LLM reviewer in the release notes.
