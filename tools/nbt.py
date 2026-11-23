"""Minimal NBT writer/reader (gzip, big-endian) for structure templates. No dependencies."""
import gzip
import struct
from pathlib import Path


class Byte(int): ID = 1
class Short(int): ID = 2
class Int(int): ID = 3
class Long(int): ID = 4
class Float(float): ID = 5
class Double(float): ID = 6
class String(str): ID = 8


class List(list):
    ID = 9

    def __init__(self, elem_type, items):
        super().__init__(items)
        self.elem_type = elem_type


class Compound(dict):
    ID = 10


_FMT = {1: ">b", 2: ">h", 3: ">i", 4: ">q", 5: ">f", 6: ">d"}


def _str(s):
    b = s.encode("utf-8")
    return struct.pack(">H", len(b)) + b


def _payload(v):
    if isinstance(v, String):
        return _str(v)
    if isinstance(v, List):
        elem_id = v.elem_type.ID if v else (v.elem_type.ID if v.elem_type is not Compound else 0)
        if not v:
            elem_id = 0
        return struct.pack(">bi", elem_id, len(v)) + b"".join(_payload(x) for x in v)
    if isinstance(v, Compound):
        out = b""
        for k, x in v.items():
            out += struct.pack(">b", x.ID) + _str(k) + _payload(x)
        return out + b"\x00"
    return struct.pack(_FMT[v.ID], v)


def write(path, root: Compound) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    data = struct.pack(">b", Compound.ID) + _str("") + _payload(root)
    with gzip.GzipFile(path, "wb", mtime=0) as f:
        f.write(data)


def read(path):
    data = gzip.decompress(Path(path).read_bytes())
    pos = 0

    def take(n):
        nonlocal pos
        b = data[pos:pos + n]
        pos += n
        return b

    def rstr():
        (n,) = struct.unpack(">H", take(2))
        return take(n).decode("utf-8")

    def rpay(t):
        if t in _FMT:
            fmt = _FMT[t]
            return struct.unpack(fmt, take(struct.calcsize(fmt)))[0]
        if t == 8:
            return rstr()
        if t == 9:
            et, n = struct.unpack(">bi", take(5))
            return [rpay(et) for _ in range(n)]
        if t == 10:
            out = {}
            while True:
                (ct,) = struct.unpack(">b", take(1))
                if ct == 0:
                    return out
                k = rstr()
                out[k] = rpay(ct)
        raise ValueError(f"unsupported tag {t}")

    (t,) = struct.unpack(">b", take(1))
    rstr()
    return rpay(t)
