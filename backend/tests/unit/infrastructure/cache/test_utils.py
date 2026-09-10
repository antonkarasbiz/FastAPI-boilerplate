import pytest

from src.infrastructure.cache.exceptions import (
    CacheIdentificationInferenceError,
)
from src.infrastructure.cache.utils import (
    format_extra_data,
    format_prefix,
    infer_resource_id,
)


def test_infer_resource_id_integer():
    kwargs = {"user_id": 123, "other_param": "value"}
    resource_id = infer_resource_id(kwargs=kwargs, resource_id_type=int)
    assert resource_id == 123


def test_infer_resource_id_string():
    kwargs = {"product_id": "abc123", "other_param": 456}
    resource_id = infer_resource_id(kwargs=kwargs, resource_id_type=str)
    assert resource_id == "abc123"


def test_infer_resource_id_multiple_types():
    kwargs = {"id": "abc123", "other_param": 456}
    resource_id = infer_resource_id(kwargs=kwargs, resource_id_type=(str, int))
    assert resource_id == "abc123"

    kwargs = {"id": 789, "other_param": "value"}
    resource_id = infer_resource_id(kwargs=kwargs, resource_id_type=(str, int))
    assert resource_id == 789


def test_infer_resource_id_no_match():
    kwargs = {"param1": "value1", "param2": "value2"}
    with pytest.raises(CacheIdentificationInferenceError):
        infer_resource_id(kwargs=kwargs, resource_id_type=int)


def test_format_prefix_simple():
    prefix = "user"
    kwargs = {"user_id": 123}
    formatted = format_prefix(prefix, kwargs)
    assert formatted == "user"


def test_format_prefix_with_variables():
    prefix = "user:{user_id}:profile"
    kwargs = {"user_id": 123, "other_param": "value"}
    formatted = format_prefix(prefix, kwargs)
    assert formatted == "user:123:profile"


def test_format_prefix_with_multiple_variables():
    prefix = "org:{org_id}:user:{user_id}"
    kwargs = {"org_id": 456, "user_id": 123}
    formatted = format_prefix(prefix, kwargs)
    assert formatted == "org:456:user:123"


def test_format_extra_data_simple():
    extra_data = {"user": "user_id"}
    kwargs = {"user_id": 123}
    formatted = format_extra_data(extra_data, kwargs)
    assert formatted == {"user": 123}


def test_format_extra_data_multiple():
    extra_data = {"user": "user_id", "org": "org_id"}
    kwargs = {"user_id": 123, "org_id": 456}
    formatted = format_extra_data(extra_data, kwargs)
    assert formatted == {"user": 123, "org": 456}


def test_format_extra_data_missing_key():
    extra_data = {"user": "user_id", "org": "org_id"}
    kwargs = {"user_id": 123}
    formatted = format_extra_data(extra_data, kwargs)
    assert formatted == {"user": 123}
    assert "org" not in formatted
