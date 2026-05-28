import sys

from dictation.config import Config, default_hotkey, load_config, write_default_config


def test_defaults_have_expected_values():
    cfg = Config()
    assert cfg.model == "base.en"
    assert cfg.sample_rate == 16000
    assert cfg.output_mode == "paste"
    assert cfg.min_duration > 0


def test_default_hotkey_is_platform_appropriate():
    hk = default_hotkey()
    if sys.platform == "darwin":
        assert hk == "right_cmd"
    else:
        assert hk == "right_ctrl"


def test_from_dict_ignores_unknown_keys_and_overrides_known():
    cfg = Config.from_dict({"model": "small.en", "totally_unknown": 123})
    assert cfg.model == "small.en"
    # Untouched keys keep their defaults.
    assert cfg.sample_rate == 16000


def test_roundtrip_yaml(tmp_path):
    path = tmp_path / "config.yaml"
    write_default_config(path)
    assert path.is_file()
    cfg = load_config(path)
    assert isinstance(cfg, Config)
    assert cfg.model == "base.en"


def test_load_missing_file_returns_defaults(tmp_path):
    cfg = load_config(tmp_path / "does-not-exist.yaml")
    assert cfg.model == Config().model
