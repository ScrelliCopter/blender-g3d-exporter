# <pep8 compliant>

import json
from json.encoder import encode_basestring_ascii, encode_basestring, INFINITY
import collections


class G3DJsonEncoder(json.JSONEncoder):
    """ Json encoder that can print N non-list values before indenting """

    float_round = 6
    float_format = None

    def __init__(self, skipkeys=False, ensure_ascii=True,
                 check_circular=True, allow_nan=True, sort_keys=False,
                 indent=None, separators=None, default=None, float_round=6):
        self.float_round = float_round
        self.float_format = "%" + \
            str(self.float_round + 3) + "." + str(self.float_round) + "f"

        super().__init__(skipkeys=skipkeys, ensure_ascii=ensure_ascii,
                         check_circular=check_circular, allow_nan=allow_nan, sort_keys=sort_keys,
                         indent=indent, separators=separators, default=default)

    def iterencode(self, o, _one_shot=False):
        """
        Encode the given object and yield each string
        representation as available.

        For example::

            for chunk in JSONEncoder().iterencode(bigobject):
                mysocket.write(chunk)

        """
        if self.check_circular:
            markers = {}
        else:
            markers = None
        if self.ensure_ascii:
            _encoder = encode_basestring_ascii
        else:
            _encoder = encode_basestring

        def floatstr(o, allow_nan=self.allow_nan,
                     _repr=float.__repr__, _inf=INFINITY, _neginf=-INFINITY):
            """
             *** Overwrites JSONEncoder.iterencode.floatstr to round floats before returning
            """

            # Check for specials.  Note that this type of test is processor
            # and/or platform-specific, so do tests which don't depend on the
            # internals.

            if o != o:
                text = 'NaN'
            elif o == _inf:
                text = 'Infinity'
            elif o == _neginf:
                text = '-Infinity'
            else:
                return self.float_format % o

            if not allow_nan:
                raise ValueError(
                    "Out of range float values are not JSON compliant: " +
                    repr(o))

            return text

        _iterencode = self._make_iterencode_g3d(
            markers, self.default, _encoder, self.indent, floatstr,
            self.key_separator, self.item_separator, self.sort_keys,
            self.skipkeys, _one_shot)
        return _iterencode(o, 0)

    def _count_indent_g3d(self, json_mesh_value):
        count_value = 0
        default_count_value = 12

        if json_mesh_value is not None \
                and (isinstance(json_mesh_value, dict) or isinstance(json_mesh_value, collections.OrderedDict)) \
                and "attributes" in json_mesh_value.keys():
            for attribute in json_mesh_value["attributes"]:
                if attribute == "POSITION" or attribute == "NORMAL" \
                        or attribute == "TANGENT" or attribute == "BINORMAL":
                    count_value = count_value + 3
                elif attribute == "COLOR":
                    count_value = count_value + 4
                elif attribute == "COLORPACKED":
                    count_value = count_value + 1
                elif attribute.startswith("TEXCOORD") or attribute.startswith("BLENDWEIGHT"):
                    count_value = count_value + 2

        if count_value != 0:
            return count_value
        else:
            return default_count_value

    def _make_iterencode_g3d(self, markers, _default, _encoder, _indent, _floatstr,
                             _key_separator, _item_separator, _sort_keys, _skipkeys, _one_shot):
        """
        *** Overwrites json.encoder._make_iterencode
        """

        if _indent is not None and not isinstance(_indent, str):
            _indent = ' ' * _indent

        def _iterencode_list(lst, _current_indent_level, _indentate=12):
            if not lst:
                yield '[]'
                return
            if markers is not None:
                markerid = id(lst)
                if markerid in markers:
                    raise ValueError("Circular reference detected")
                markers[markerid] = lst
            buf = '['
            _current_indent_level += 1
            newline_indent = '\n' + _indent * _current_indent_level
            separator = _item_separator + newline_indent
            buf += newline_indent
            first = True
            lastWasList = False
            current_break = 0
            for value in lst:
                if first:
                    first = False
                elif lastWasList:
                    buf = separator
                elif not lastWasList and current_break >= _indentate:
                    current_break = 0
                    buf = separator
                else:
                    buf = _item_separator

                if isinstance(value, str):
                    yield buf + _encoder(value)
                    lastWasList = False
                    current_break = current_break + 1
                elif value is None:
                    yield buf + 'null'
                    lastWasList = False
                    current_break = current_break + 1
                elif value is True:
                    yield buf + 'true'
                    lastWasList = False
                    current_break = current_break + 1
                elif value is False:
                    yield buf + 'false'
                    lastWasList = False
                    current_break = current_break + 1
                elif isinstance(value, int):
                    yield buf + str(value)
                    lastWasList = False
                    current_break = current_break + 1
                elif isinstance(value, float):
                    yield buf + _floatstr(value)
                    lastWasList = False
                    current_break = current_break + 1
                else:
                    yield buf
                    lastWasList = True
                    current_break = 0
                    if isinstance(value, (list, tuple)):
                        chunks = _iterencode_list(value, _current_indent_level)
                    elif isinstance(value, dict):
                        chunks = _iterencode_dict(
                            value, _current_indent_level, _list_indent=self._count_indent_g3d(value))
                    else:
                        chunks = _iterencode(value, _current_indent_level)
                    for chunk in chunks:
                        yield chunk
            _current_indent_level -= 1
            yield '\n' + _indent * _current_indent_level
            yield ']'
            if markers is not None:
                del markers[markerid]

        def _iterencode_dict(dct, _current_indent_level, _list_indent=12):
            if not dct:
                yield '{}'
                return
            if markers is not None:
                markerid = id(dct)
                if markerid in markers:
                    raise ValueError("Circular reference detected")
                markers[markerid] = dct
            yield '{'
            _current_indent_level += 1
            newline_indent = '\n' + _indent * _current_indent_level
            item_separator = _item_separator + newline_indent
            yield newline_indent
            first = True
            items = dct.items()
            for key, value in items:
                if isinstance(key, str):
                    pass
                elif isinstance(key, float):
                    key = _floatstr(key)
                elif key is True:
                    key = 'true'
                elif key is False:
                    key = 'false'
                elif key is None:
                    key = 'null'
                elif isinstance(key, int):
                    key = str(key)
                elif _skipkeys:
                    continue
                else:
                    raise TypeError("key " + repr(key) + " is not a string")
                if first:
                    first = False
                else:
                    yield item_separator
                yield _encoder(key)
                yield _key_separator
                if isinstance(value, str):
                    yield _encoder(value)
                elif value is None:
                    yield 'null'
                elif value is True:
                    yield 'true'
                elif value is False:
                    yield 'false'
                elif isinstance(value, int):
                    yield str(value)
                elif isinstance(value, float):
                    yield _floatstr(value)
                else:
                    if isinstance(value, (list, tuple)):
                        chunks = _iterencode_list(
                            value, _current_indent_level, _indentate=_list_indent)
                    elif isinstance(value, dict):
                        chunks = _iterencode_dict(
                            value, _current_indent_level, _list_indent=self._count_indent_g3d(value))
                    else:
                        chunks = _iterencode(
                            value, _current_indent_level, _obj_indent=self._count_indent_g3d(value))
                    for chunk in chunks:
                        yield chunk
            _current_indent_level -= 1
            yield '\n' + _indent * _current_indent_level
            yield '}'
            if markers is not None:
                del markers[markerid]

        def _iterencode(o, _current_indent_level, _obj_indent=12):
            if isinstance(o, str):
                yield _encoder(o)
            elif o is None:
                yield 'null'
            elif o is True:
                yield 'true'
            elif o is False:
                yield 'false'
            elif isinstance(o, int):
                yield str(o)
            elif isinstance(o, float):
                yield _floatstr(o)
            elif isinstance(o, (list, tuple)):
                for chunk in _iterencode_list(o, _current_indent_level, _indentate=_obj_indent):
                    yield chunk
            elif isinstance(o, dict):
                for chunk in _iterencode_dict(o, _current_indent_level, _list_indent=self._count_indent_g3d(o)):
                    yield chunk
            else:
                raise ValueError('Type not supported: ' + type(o))
        return _iterencode
