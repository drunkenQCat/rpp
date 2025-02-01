from collections.abc import Iterable
from typing import SupportsIndex, Union  # pyright: ignore[reportDeprecated]
import xml.etree.ElementPath

import attr


@attr.s
class Element:
    tag: str = attr.ib()
    attrib: dict[str, str] = attr.ib(default={})
    children: list["Element"] = attr.ib(default=attr.Factory(list["Element"]))

    def append(self, element: "Element"):
        self.children.append(element)

    def extend(self, elements: Iterable["Element"]):
        self.children.extend(elements)

    def insert(self, index: SupportsIndex, element: "Element"):
        self.children.insert(index, element)

    def remove(self, element: "Element"):
        self.children.remove(element)

    def findall(self, path: str):
        return list(self.iterfind(path))

    def find(self, path: str):
        return next(self.iterfind(path), None)

    def iterfind(self, path: str):
        queryable_element = QueryableElement(self)
        found = xml.etree.ElementPath.iterfind(queryable_element, path)  # pyright: ignore[reportArgumentType]
        for item in found:
            if isinstance(item, ListBackedElement):
                yield item.element_list
            elif isinstance(item, QueryableElement):
                yield item.element

    def iter(self, tag: str | None = None):
        return iterate_element(self, tag)

    def __iter__(self):
        return iter(self.children)

    def __getitem__(self, index: SupportsIndex):
        return self.children[index]

    def __setitem__(self, index: SupportsIndex, element: "Element"):
        self.children[index] = element

    def __len__(self):
        return len(self.children)


@attr.s
class ListBackedElement:
    element_list: list[str] = attr.ib()

    @property
    def tag(self):
        return self.element_list[0]

    def iter(self, tag: str | None = None):
        if tag is None or self.tag == tag:
            yield self

    def __iter__(self):
        return iter(())


@attr.s
class QueryableElement:
    element: Element | list[float | int | str] = attr.ib()

    @property
    def tag(self) -> str:
        if isinstance(self.element, Element):
            return self.element.tag
        else:
            return ""

    def iter(self, tag: str | None = None) -> Iterable["QueryableElement"]:
        return iterate_element(self, tag)

    def __iter__(self) -> Iterable[Union["QueryableElement", ListBackedElement]]:
        for item in self.element:
            if isinstance(item, Element):
                yield QueryableElement(item)
            elif isinstance(item, list):
                yield ListBackedElement(item)


def iterate_element(element, tag):
    if tag is None or element.tag == tag:
        yield element
    for item in element:
        if hasattr(item, "iter"):
            yield from item.iter(tag)
        elif tag is None:
            yield item
