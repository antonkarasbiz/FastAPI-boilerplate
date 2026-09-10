import re
from typing import Any

from .exceptions import CacheIdentificationInferenceError


def infer_resource_id(kwargs: dict[str, Any], resource_id_type: type | tuple[type, ...]) -> int | str:
    """Infer the resource ID from a dictionary of keyword arguments.

    Args:
        kwargs: A dictionary of keyword arguments.
        resource_id_type: The expected type of the resource ID (int, str, or tuple of types).

    Returns:
        The inferred resource ID.

    Raises:
        CacheIdentificationInferenceError: If the resource ID cannot be inferred.
    """
    if not isinstance(resource_id_type, tuple):
        resource_id_type = (resource_id_type,)

    for arg_name, arg_value in kwargs.items():
        if "id" in arg_name.lower() and any(isinstance(arg_value, t) for t in resource_id_type):
            if isinstance(arg_value, int | str):
                return arg_value
            return str(arg_value)

    for arg_name, arg_value in kwargs.items():
        if any(isinstance(arg_value, t) for t in resource_id_type):
            if isinstance(arg_value, int | str):
                return arg_value
            return str(arg_value)

    raise CacheIdentificationInferenceError()


def extract_data_inside_brackets(input_string: str) -> list[str]:
    """Extract data inside curly brackets from a given string.

    Args:
        input_string: The input string containing data in curly brackets.

    Returns:
        A list of strings found inside curly brackets.
    """
    data_inside_brackets = re.findall(r"{(.*?)}", input_string)
    return data_inside_brackets


def construct_data_dict(data_inside_brackets: list[str], kwargs: dict[str, Any]) -> dict[str, Any]:
    """Construct a dictionary based on data inside brackets and keyword arguments.

    Args:
        data_inside_brackets: A list of keys found inside brackets.
        kwargs: A dictionary of keyword arguments.

    Returns:
        A dictionary with keys from data_inside_brackets and values from kwargs.
    """
    data_dict = {}
    for key in data_inside_brackets:
        if key not in kwargs:
            continue
        data_dict[key] = kwargs[key]
    return data_dict


def format_prefix(prefix: str, kwargs: dict[str, Any]) -> str:
    """Format a prefix using keyword arguments.

    Args:
        prefix: The prefix template to format.
        kwargs: A dictionary of keyword arguments.

    Returns:
        The formatted prefix.
    """
    data_inside_brackets = extract_data_inside_brackets(prefix)
    data_dict = construct_data_dict(data_inside_brackets, kwargs)
    formatted_prefix = prefix.format(**data_dict)
    return formatted_prefix


def format_extra_data(to_invalidate_extra: dict[str, str], kwargs: dict[str, Any]) -> dict[str, Any]:
    """Format extra data for cache invalidation.

    Args:
        to_invalidate_extra: A dictionary of cache key prefixes and ID templates.
        kwargs: A dictionary of keyword arguments.

    Returns:
        A dictionary of formatted prefixes and IDs.
    """
    formatted_extra = {}
    for prefix, id_name in to_invalidate_extra.items():
        if id_name in kwargs:
            formatted_extra[prefix] = kwargs[id_name]
            continue

        if "{" in id_name:
            id_vars = extract_data_inside_brackets(id_name)
            if not id_vars:
                continue

            id_var = id_vars[0]
            if id_var in kwargs:
                formatted_id = id_name.format(**{id_var: kwargs[id_var]})
                formatted_extra[prefix] = formatted_id

    return formatted_extra
