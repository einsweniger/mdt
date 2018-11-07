from pathlib import PurePath

class InvalidStateException(Exception):
    def __init__(self) -> None:
        super().__init__('top of stack has wrong type or empty')


class ParserStack:
    def __init__(self) -> None:
        self.stacks = []

    def push_element(self, element):
        if not self.top_is_list:
            raise InvalidStateException
        self.stacks[-1].append(element)

    def push_kv(self, key, value):
        if not self.top_is_dict:
            raise InvalidStateException
        self.stacks[-1][key] = value

    def add_object_stack(self):
        self.stacks.append(dict())

    def add_array_stack(self):
        self.stacks.append(list())

    def pop_dict(self) -> dict:
        if not self.top_is_dict:
            raise InvalidStateException
        return self.stacks.pop()

    def pop_list(self) -> list:
        if not self.top_is_list:
            raise InvalidStateException
        return self.stacks.pop()

    @property
    def top_is_dict(self) -> bool:
        if 0 == len(self.stacks):
            return False
        return isinstance(self.stacks[-1], dict)

    @property
    def top_is_list(self) -> bool:
        if 0 == len(self.stacks):
            return False
        return isinstance(self.stacks[-1], list)


class ResultSetEmitter:

    def __init__(self):
        self.stacks = ParserStack()
        self.xpath_current = PurePath()
        self.result = None

    def _on_object_start(self):
        self.stacks.add_object_stack()

    def _on_object_end(self):
        content = self.stacks.pop_dict()

        if self.stacks.top_is_list:
            self._on_element(content)
            return
        if self.stacks.top_is_dict:
            self._on_value(content)
            return
        if self.result:
            raise ValueError('result already set')
        self.result = content

    def _on_array_start(self):
        """
        this will be called by the streaming parser.
        we open up a new deque and push all further content into it.
        this new deque will be removed when the streaming parser calls _on_array_end
        :return: nothing
        """
        self.stacks.add_array_stack()

    def _on_array_end(self):
        """
        this will be called by the streaming parser.
        once an array is finished we pop the upper deque and use its collected contents as an array
        :return: nothing
        """
        content = self.stacks.pop_list()

        if self.stacks.top_is_dict:
            self._on_value(content)
            return
        if self.stacks.top_is_list:
            self._on_element(content)
            return
        if self.result:
            raise ValueError('result already set')
        self.result = content

    def _on_key(self, name: str):
        """
        this will be called by the streaming parser when a new k/v pair starts

        we push the name on the current hierarchy.
        once the corresponding value is completely parsed, it will pop the name for the value.
        :param name: the name of the key
        :return: nothing
        """
        self.xpath_current /= name

    def _on_value(self, value):
        """
        this function receives something that is part of a k/v pair, there are two cases:

        for simple k/v pairs (as in {"key": "value"}):
        this will be called from the streaming parser, right after _on_key

        for nested objects (as in {"key": {x:y}}, with value = {x:y}):
        this method will be called from _on_array_end or _on_object_end.

        :param value: the value to be attached to an object
        :return: nothing
        """
        name = self.xpath_current.stem
        # pop the current name from the xpath
        self.xpath_current = self.xpath_current.parent
        self.stacks.push_kv(name, value)

    def _on_element(self, value):
        """
        this will be called by the streaming parser, as long as we are in an array.
        the value will be a simple type of an array, so we simply append it to the upper deque.
        :param value:
        :return:
        """
        self.stacks.push_element(value)