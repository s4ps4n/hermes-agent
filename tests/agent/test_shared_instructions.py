"""``SHARED_INSTRUCTIONS.md`` at the Hermes ROOT is operator policy for EVERY profile.

The default profile, each existing named profile and a profile created later must all read
the same file — no per-profile copies. Regression guard for a per-installation resource
policy (e.g. "heavy compute goes to the remote node, never the gateway VPS").
"""
from types import SimpleNamespace

POLICY = "RESOURCE POLICY: heavy tests/builds run on the remote compute node, never on this VPS."


def _make_root(tmp_path):
    root = tmp_path / ".hermes"
    root.mkdir()
    (root / "SHARED_INSTRUCTIONS.md").write_text(POLICY, encoding="utf-8")
    return root


def test_default_profile_reads_shared_policy(tmp_path):
    from agent import prompt_builder

    root = _make_root(tmp_path)
    assert prompt_builder.load_shared_instructions_md(home_override=root) == POLICY


def test_existing_named_profile_reads_shared_policy(tmp_path):
    from agent import prompt_builder

    root = _make_root(tmp_path)
    papa = root / "profiles" / "papa"
    papa.mkdir(parents=True)
    (papa / "SOUL.md").write_text("papa persona", encoding="utf-8")

    assert prompt_builder.load_shared_instructions_md(home_override=papa) == POLICY


def test_new_profile_inherits_shared_policy(tmp_path, monkeypatch):
    from agent import prompt_builder
    from hermes_cli.profiles import create_profile

    root = _make_root(tmp_path)
    monkeypatch.setenv("HERMES_HOME", str(root))
    newbie = create_profile("newbie", no_skills=True, no_alias=True)

    # Nothing was copied into the profile: it reads the ROOT file like every other profile.
    assert not (newbie / "SHARED_INSTRUCTIONS.md").exists()
    assert prompt_builder.load_shared_instructions_md(home_override=newbie) == POLICY


def test_profile_local_file_is_not_a_shared_policy_source(tmp_path):
    from agent import prompt_builder

    root = tmp_path / ".hermes"
    papa = root / "profiles" / "papa"
    papa.mkdir(parents=True)
    (papa / "SHARED_INSTRUCTIONS.md").write_text("profile-local text", encoding="utf-8")

    assert prompt_builder.load_shared_instructions_md(home_override=papa) is None


def test_identity_parts_carry_shared_policy(tmp_path):
    from agent import prompt_builder
    from agent.system_prompt import _identity_parts

    root = _make_root(tmp_path)
    papa = root / "profiles" / "papa"
    papa.mkdir(parents=True)
    agent = SimpleNamespace(
        load_soul_identity=True,
        skip_context_files=False,
        _session_db=SimpleNamespace(db_path=str(papa / "state.db")),
    )
    parts, soul_loaded = _identity_parts(agent, None)

    assert soul_loaded is False  # no SOUL.md -> default identity, policy still applies
    assert any(POLICY in part for part in parts)


def test_missing_shared_file_returns_none(tmp_path):
    from agent import prompt_builder

    assert prompt_builder.load_shared_instructions_md(home_override=tmp_path) is None
