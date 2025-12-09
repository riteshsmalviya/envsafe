import os

from envsafe import Env, env, EnvError


def test_str_required_missing():
    local_env = Env(source={})
    try:
        local_env.str("MISSING", required=True)
        assert False, "Expected EnvError"
    except EnvError:
        assert True


def test_int_with_bounds():
    local_env = Env(source={"PORT": "8080"})
    value = local_env.int("PORT", min=1, max=9000)
    assert value == 8080


def test_bool_parsing():
    local_env = Env(source={"DEBUG": "true", "FLAG": "0"})
    assert local_env.bool("DEBUG") is True
    assert local_env.bool("FLAG") is False


def test_url_validation():
    local_env = Env(source={"DATABASE_URL": "postgres://user@localhost/db"})
    value = local_env.url("DATABASE_URL", schemes=["postgres"])
    assert value.startswith("postgres://")


def test_choice_case_insensitive():
    local_env = Env(source={"ENV": "Prod"})
    value = local_env.choice("ENV", choices=["dev", "staging", "prod"])
    assert value == "prod"


def test_list_parsing():
    local_env = Env(source={"ALLOWED_HOSTS": "a.com, b.com, c.com"})
    hosts = local_env.list("ALLOWED_HOSTS")
    assert hosts == ["a.com", "b.com", "c.com"]


def test_default_instance_uses_os_environ(monkeypatch):
    monkeypatch.setenv("DEBUG", "1")
    assert env.bool("DEBUG") is True
