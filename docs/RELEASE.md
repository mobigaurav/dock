# How to publish Dock (`dock-inbox`)

Product and CLI: **Dock**. PyPI name: **`dock-inbox`**. Import package: `dock`.

`pip install dock` must never be the instruction — that name is a molecule-docking toolkit.

## First release (v0.1.0)

1. Merge this work to `main` and `git tag v0.1.0 && git push origin main --tags`.
2. Create a GitHub Release from that tag.
3. PyPI trusted publishing (one-time in the browser, then re-run the failed `pypi` workflow):
   - Log in at [pypi.org](https://pypi.org/account/login/).
   - [Pending publishers](https://pypi.org/manage/account/publishing/) → add **dock-inbox**:
     - Owner: `mobigaurav`
     - Repository: `dock`
     - Workflow: `pypi.yml`
     - Environment: `pypi`
   - Re-run [the v0.1.0 publish job](https://github.com/mobigaurav/dock/actions). First upload creates the project.
4. Verify: `pip install dock-inbox==0.1.0 && dock --help`
5. Point Arogya’s `.github/workflows/dock.yml` at `pip install dock-inbox==0.1.0` instead of `git+https`.

## v0.1.1

Dogfood from Arogya PRs (#51, #53, #54, #55):

- Skip the entire Test plan / checklist / QA section. A how-to-test bullet that names `_deps.py` is not a Summary claim and must not pass.
- Pass when a claim names a directory (`apps/mobile`) and a child path is in the diff.
- Pass when a backticked code token (`SignInWithApple`) appears in the patch; unknown if it does not (console-only config).
- Empty or generic bodies (`new changes`) fall back to commit messages so dest→main promotion PRs still have something to score.

Tag `v0.1.1`, GitHub Release, wait for `pypi.yml`, then pin Arogya to `dock-inbox==0.1.1`.

## What other developers run

```bash
pip install dock-inbox
```

Copy `examples/github-inbox.yml` to `.github/workflows/dock.yml`. They need `gh` locally for `dock merge --pr`; GitHub Actions uses `GITHUB_TOKEN`.

## Do not

- Upload as `dock` or `agentdock` (taken).
- Pin CI to `@main`.
- Promise an LLM reviewer in the release notes.
