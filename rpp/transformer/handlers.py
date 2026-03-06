"""Handler functions for RPP transformer.

Provides specific handlers for complex transformation cases like element creation
and struct content processing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


from .utils import is_token, merge_split_values, merge_pending_floats

if TYPE_CHECKING:
    pass


def handle_element_children(children: list, tag: str) -> list:
    """Process and extract child elements from parse tree children.

    Args:
        children: Parse tree children from element rule.
        tag: The element tag name.

    Returns:
        List of processed child elements.
    """
    result = []

    for child in children:
        # Skip tokens
        if is_token(child):
            continue

        # Skip struct and empty lists
        if not isinstance(child, list) or len(child) == 0:
            continue

        # Skip struct (compare first element)
        if child[0] == tag:
            continue

        # Process content_lines
        if child and isinstance(child, list):
            for content_item in child:
                result.append(_process_content_item(content_item))
        else:
            result.append(child)

    return result


def _process_content_item(content_item):
    """Process a single content item from content_lines.

    Args:
        content_item: The content item to process.

    Returns:
        Processed content item.
    """
    if not isinstance(content_item, list):
        return content_item

    # Check if it looks like struct_content or compressed
    if content_item and isinstance(content_item[0], str):
        first = content_item[0]
        # struct_content: [TAG, attr1, attr2, ...] - first element is uppercase
        # compressed: [base64_str1, base64_str2, ...] - first element is not uppercase
        if first.isupper() and len(content_item) > 1:
            # This is struct_content
            return content_item

    # This is compressed result or other list
    return content_item


def handle_struct_as_content(children: list) -> list[str]:
    """Process struct as content (not inside element).

    Args:
        children: Parse tree children [tag_tree, attr_list_tree].

    Returns:
        List of strings [tag, attr1, attr2, ...].
    """
    tag = children[0]
    attr_list = list(children[1])  # Make a copy to avoid modifying original

    # Handle RENDER_1X pattern
    tag, attr_list = _merge_render_tag(tag, attr_list)

    # Handle SELECTION2 pattern
    tag, attr_list = _merge_selection_tag(tag, attr_list)

    # Merge PendingFloats
    attr_list = merge_pending_floats(attr_list)

    # Merge split values (skip if tag already in attr_list)
    if tag not in attr_list:
        attr_list = merge_split_values(attr_list)

    # Build result
    result: list[str] = [tag]
    for param in attr_list:
        result.append(str(param))

    return result


def _merge_render_tag(tag: str, attr_list: list) -> tuple[str, list]:
    """Merge RENDER_ + digit + optional uppercase pattern.

    Args:
        tag: Current tag.
        attr_list: List of attributes.

    Returns:
        Tuple of (updated_tag, updated_attr_list).
    """
    if not tag.endswith("_") or len(attr_list) < 1:
        return tag, attr_list

    first_attr = str(attr_list[0])
    if not first_attr.isdigit():
        return tag, attr_list

    merged = tag + first_attr

    # Check for uppercase suffix
    if len(attr_list) >= 2:
        second_attr = str(attr_list[1])
        if second_attr.isupper() and len(second_attr) <= 4:
            merged += second_attr
            return merged, list(attr_list[2:])

    return merged, list(attr_list[1:])


def _merge_selection_tag(tag: str, attr_list: list) -> tuple[str, list]:
    """Merge SELECTION + multi-digit number pattern.

    Args:
        tag: Current tag.
        attr_list: List of attributes.

    Returns:
        Tuple of (updated_tag, updated_attr_list).
    """
    if tag != "SELECTION" or len(attr_list) < 1:
        return tag, attr_list

    first_attr = str(attr_list[0])
    if not (first_attr.isdigit() and len(first_attr) >= 2):
        return tag, attr_list

    merged = tag + first_attr
    return merged, list(attr_list[1:])


def handle_attr_list(children: list) -> list[str]:
    """Process attribute list with PendingFloat merging.

    Args:
        children: List of attribute values.

    Returns:
        List of processed attribute strings.
    """
    result = []

    for child in children:
        # Check for PendingFloat that needs merging with previous value
        if result and hasattr(child, "is_real_float") and not child.is_real_float:
            prev = result[-1]
            if isinstance(prev, str) and (prev.isdigit() or prev.startswith("-")):
                merged = prev + child.value
                result[-1] = merged
                continue
        result.append(child)

    # Post-process: merge split values and convert to strings
    result = merge_split_values(result)
    return [str(c) for c in result]


def handle_content_lines(children: list) -> list:
    """Process content_lines rule children.

    Args:
        children: Parse tree children with content and NEWLINE tokens.

    Returns:
        List of content items.
    """
    result = []

    for item in children:
        if is_token(item):
            continue

        # Handle list items (from compressed or other rules)
        if isinstance(item, list):
            result.append(_wrap_list_if_needed(item))
        else:
            result.append(item)

    return result


def _wrap_list_if_needed(item: list) -> list:
    """Wrap list items appropriately based on content.

    Args:
        item: The list item to process.

    Returns:
        Processed list item.
    """
    if not item or not isinstance(item[0], str):
        return item

    first = item[0]
    # If first element is not uppercase, it's likely compressed data
    if not first.isupper():
        return item

    return item
