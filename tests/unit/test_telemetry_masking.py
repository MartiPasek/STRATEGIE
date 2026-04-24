"""
Unit tests pro telemetry_service masking (Faze 9.1).

Testuje mask_secrets() a _mask_string() -- zajisti, ze secrets nepronikaji
do llm_calls tabulky.

Neotestuje DB zapis (to je integracni test). Nepouziva zivy anthropic API.
"""
from modules.conversation.application.telemetry_service import (
    mask_secrets,
    _mask_string,
    _is_sensitive_key,
)


# ── _is_sensitive_key ──────────────────────────────────────────────────────

def test_sensitive_key_password():
    assert _is_sensitive_key("password")
    assert _is_sensitive_key("Password")
    assert _is_sensitive_key("PASSWORD")
    assert _is_sensitive_key("user_password")
    assert _is_sensitive_key("password_encrypted")


def test_sensitive_key_api_key():
    assert _is_sensitive_key("api_key")
    assert _is_sensitive_key("anthropic_api_key")
    assert _is_sensitive_key("apikey")
    assert _is_sensitive_key("voyage_api_key")


def test_sensitive_key_tokens():
    # Konkretni *_token varianty matchuji:
    assert _is_sensitive_key("access_token")
    assert _is_sensitive_key("refresh_token")
    assert _is_sensitive_key("bearer_token")
    assert _is_sensitive_key("session_token")
    assert _is_sensitive_key("authorization")
    assert _is_sensitive_key("Authorization")
    assert _is_sensitive_key("X-Api-Key")


def test_sensitive_key_max_tokens_NOT_matched():
    # max_tokens / input_tokens / output_tokens jsou legitimni Anthropic
    # API pole, NESMI byt maskovane. Bug opraven -- "token" bez prefixu
    # jiz neni v _SENSITIVE_KEY_PATTERNS.
    assert not _is_sensitive_key("max_tokens")
    assert not _is_sensitive_key("input_tokens")
    assert not _is_sensitive_key("output_tokens")
    assert not _is_sensitive_key("prompt_tokens")


def test_sensitive_key_encryption():
    assert _is_sensitive_key("encryption_key")
    assert _is_sensitive_key("ENCRYPTION_KEY")
    assert _is_sensitive_key("fernet_secret")


def test_sensitive_key_login_upn_column():
    # persona_channels.identifier sam o sobe neni v sensitive list
    # (nema dobry keyword), maskuje se pres regex v _mask_string.
    # Ale identifier_secret ano:
    assert _is_sensitive_key("identifier_secret")


def test_sensitive_key_normal_keys_not_flagged():
    assert not _is_sensitive_key("name")
    assert not _is_sensitive_key("email")
    assert not _is_sensitive_key("message")
    assert not _is_sensitive_key("content")
    assert not _is_sensitive_key("model")
    assert not _is_sensitive_key("user_id")


# ── _mask_string: regex patterns ───────────────────────────────────────────

def test_mask_anthropic_api_key():
    s = "Authorization: sk-ant-api03-abc123XYZ456qwerty789ABCDEF"
    out = _mask_string(s, login_upns=set())
    assert "sk-ant-" not in out
    assert "***ANTHROPIC_KEY***" in out


def test_mask_voyage_api_key():
    s = "use pa-01234567890abcdefghijklmnopqrstuv for voyage"
    out = _mask_string(s, login_upns=set())
    assert "pa-01234" not in out
    assert "***VOYAGE_KEY***" in out


def test_mask_bearer_token():
    s = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc.def"
    out = _mask_string(s, login_upns=set())
    assert "eyJhbG" not in out
    assert "***MASKED***" in out


def test_mask_login_upn_literal():
    upns = {"marti@firma.cz", "ondra@cool-co.internal"}
    s = "login as marti@firma.cz and then as Ondra@Cool-Co.Internal"
    out = _mask_string(s, login_upns=upns)
    assert "marti@firma.cz" not in out.lower()
    assert "ondra@cool-co.internal" not in out.lower()
    assert "***LOGIN_UPN***" in out


def test_mask_login_upn_case_insensitive():
    upns = {"admin@example.com"}
    s = "user: Admin@Example.COM"
    out = _mask_string(s, login_upns=upns)
    assert "Admin@Example" not in out
    assert "***LOGIN_UPN***" in out


def test_mask_preserves_normal_text():
    s = "Ahoj Marti, co delas dnes?"
    out = _mask_string(s, login_upns=set())
    assert out == s


def test_mask_empty_string():
    assert _mask_string("", login_upns=set()) == ""


# ── mask_secrets: dict/list rekurze ────────────────────────────────────────

def test_mask_dict_with_password_key():
    obj = {"name": "Marti", "password": "SuperSecret123"}
    out = mask_secrets(obj, login_upns=set())
    assert out["name"] == "Marti"
    assert out["password"] == "***MASKED***"


def test_mask_dict_with_api_key_variants():
    obj = {
        "anthropic_api_key": "sk-ant-actual-key",
        "API_KEY": "secret",
        "ApiKey": "secret",
        "x-api-key": "secret",
        "harmless_key": "abc",
    }
    out = mask_secrets(obj, login_upns=set())
    assert out["anthropic_api_key"] == "***MASKED***"
    assert out["API_KEY"] == "***MASKED***"
    assert out["ApiKey"] == "***MASKED***"
    assert out["x-api-key"] == "***MASKED***"
    assert out["harmless_key"] == "abc"


def test_mask_nested_dict():
    obj = {
        "request": {
            "headers": {
                "authorization": "Bearer token_xyz",
                "content-type": "application/json",
            },
            "body": {
                "user": "marti",
                "password": "hunter2",
            },
        },
    }
    out = mask_secrets(obj, login_upns=set())
    assert out["request"]["headers"]["authorization"] == "***MASKED***"
    assert out["request"]["headers"]["content-type"] == "application/json"
    assert out["request"]["body"]["user"] == "marti"
    assert out["request"]["body"]["password"] == "***MASKED***"


def test_mask_list_of_dicts():
    # Pouzivame 'access_token' (konkretni *_token variant), ne generic
    # 'token' -- generic nematchuje kvuli anti-regression na max_tokens
    # (Anthropic legitimni pole, viz test_sensitive_key_max_tokens_NOT_matched).
    obj = [
        {"name": "alice", "access_token": "t1"},
        {"name": "bob", "access_token": "t2"},
    ]
    out = mask_secrets(obj, login_upns=set())
    assert out[0]["access_token"] == "***MASKED***"
    assert out[1]["access_token"] == "***MASKED***"
    assert out[0]["name"] == "alice"


def test_mask_regex_on_string_values_in_dict():
    obj = {"message": "Try calling with sk-ant-api03-realkey-here-123456789"}
    out = mask_secrets(obj, login_upns=set())
    assert "sk-ant-" not in out["message"]
    assert "***ANTHROPIC_KEY***" in out["message"]


def test_mask_login_upn_in_nested_string():
    upns = {"marti@firma.cz"}
    obj = {
        "messages": [
            {"role": "user", "content": "send email to marti@firma.cz"},
            {"role": "assistant", "content": "OK, posilam"},
        ],
    }
    out = mask_secrets(obj, login_upns=upns)
    assert "marti@firma.cz" not in str(out).lower()
    assert "***LOGIN_UPN***" in out["messages"][0]["content"]


def test_mask_preserves_primitives():
    obj = {
        "count": 42,
        "ratio": 0.85,
        "enabled": True,
        "missing": None,
    }
    out = mask_secrets(obj, login_upns=set())
    assert out == obj


def test_mask_handles_empty_structures():
    assert mask_secrets({}, login_upns=set()) == {}
    assert mask_secrets([], login_upns=set()) == []
    assert mask_secrets("", login_upns=set()) == ""


def test_mask_composite_realistic():
    """
    Realisticky scenar: request_json pred zapisem do llm_calls.
    Simulace toho, co by mohlo jit do Anthropic API + content block s user
    zpravou obsahujici email adresu admina.
    """
    upns = {"marti@eurosoft.cz"}
    request = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 4096,
        "system": "Jsi Marti-AI. Login marti@eurosoft.cz nikdy neuvadej.",
        "messages": [
            {"role": "user", "content": "pošli email na marti@eurosoft.cz"},
            {"role": "assistant", "content": "OK, posilam"},
        ],
        "tools": [],
    }
    out = mask_secrets(request, login_upns=upns)

    # System prompt maskovan
    assert "marti@eurosoft.cz" not in out["system"]
    assert "***LOGIN_UPN***" in out["system"]

    # Messages maskovany
    assert "marti@eurosoft.cz" not in out["messages"][0]["content"]

    # Ostatni fields zachovany
    assert out["model"] == "claude-sonnet-4-6"
    assert out["max_tokens"] == 4096
    assert out["messages"][1]["content"] == "OK, posilam"
