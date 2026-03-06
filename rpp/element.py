from __future__ import annotations

import xml.etree.ElementPath
from dataclasses import dataclass, field
from typing import Any, Generator, Iterator, Optional, Sequence, Union


@dataclass
class Element:
    tag: str
    attrib: tuple = ()
    children: list = field(default_factory=list)

    def append(self, element: Any) -> None:
        self.children.append(element)

    def extend(self, elements: Sequence[Any]) -> None:
        self.children.extend(elements)

    def insert(self, index: int, element: Any) -> None:
        self.children.insert(index, element)

    def remove(self, element: Any) -> None:
        self.children.remove(element)

    def findall(self, path: str) -> list:
        return list(self.iterfind(path))

    def find(self, path: str) -> Optional[Any]:
        return next(self.iterfind(path), None)

    def iterfind(self, path: str) -> Generator[Any, None, None]:
        queryable_element = QueryableElement(self)
        found = xml.etree.ElementPath.iterfind(queryable_element, path)  # type: ignore[arg-type]
        for item in found:
            if isinstance(item, ListBackedElement):
                yield item.list
            elif isinstance(item, QueryableElement):
                yield item.element

    def iter(self, tag: Optional[str] = None) -> Generator[Any, None, None]:
        return iterate_element(self, tag)

    def __iter__(self) -> Iterator[Any]:
        return iter(self.children)

    def __getitem__(self, index: int) -> Any:
        return self.children[index]

    def __setitem__(self, index: int, element: Any) -> None:
        self.children[index] = element

    def __len__(self) -> int:
        return len(self.children)


@dataclass
class QueryableElement:
    element: Element

    @property
    def tag(self) -> str:
        return self.element.tag

    def iter(self, tag: Optional[str] = None) -> Generator[Any, None, None]:
        return iterate_element(self, tag)

    def __iter__(
        self,
    ) -> Generator[Union[QueryableElement, ListBackedElement], None, None]:
        for item in self.element:
            if isinstance(item, Element):
                yield QueryableElement(item)
            elif isinstance(item, list):
                yield ListBackedElement(item)


@dataclass
class ListBackedElement:
    list: list

    @property
    def tag(self) -> Any:
        return self.list[0]

    def iter(
        self, tag: Optional[str] = None
    ) -> Generator[ListBackedElement, None, None]:
        if tag is None or self.tag == tag:
            yield self

    def __iter__(self) -> Iterator[Any]:
        return iter(())


def iterate_element(element: Any, tag: Optional[str]) -> Generator[Any, None, None]:
    if tag is None or element.tag == tag:
        yield element
    for item in element:
        if hasattr(item, "iter"):
            yield from item.iter(tag)
        elif tag is None:
            yield item
