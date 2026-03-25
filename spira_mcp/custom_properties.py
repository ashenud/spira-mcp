"""Spira custom property helpers (read / table / in-place update)."""

from __future__ import annotations


def custom_property_display_value(cp: dict):
    return (
        cp.get("StringValue")
        or cp.get("IntegerValue")
        or cp.get("DecimalValue")
        or cp.get("BooleanValue")
        or cp.get("DateTimeValue")
        or cp.get("IntegerListValue")
    )


def markdown_custom_properties_table(custom_props: list) -> str:
    """Property name and current value only, as a Markdown table."""
    lines = [
        "| Property Name | Current Value |",
        "|---|---|",
    ]
    if not custom_props:
        lines.append("| _No custom properties_ | |")
    else:
        for cp in custom_props:
            defn = cp.get("Definition") or {}
            name = defn.get("Name") or f"Property {cp.get('PropertyNumber', '?')}"
            raw = custom_property_display_value(cp)
            val = "_Not set_" if raw is None else str(raw)
            lines.append(f"| {name} | {val} |")
    return "\n".join(lines)


def apply_custom_field_update(
    custom_props: list, field_name: str, field_value: str
) -> bool:
    """Mutate custom_props in place; return True if a property matched."""
    matched = False
    for cp in custom_props:
        defn = cp.get("Definition") or {}
        if defn.get("Name", "").lower() == field_name.lower():
            for vkey in (
                "StringValue",
                "IntegerValue",
                "DecimalValue",
                "BooleanValue",
                "DateTimeValue",
                "IntegerListValue",
            ):
                cp[vkey] = None
            cp["StringValue"] = field_value
            matched = True
            break
    return matched
