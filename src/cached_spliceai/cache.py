import json
import pysam
import redis


def stringify_args(*args, **kwargs) -> str:
    """
    >>> stringify_args(101, "yolo", mou="stache")
    "101|yolo|mou=stache"
    """
    args_str_list = [str(v) for v in list(args)]
    kwargs_str_list = [f"{k}={v}" for k, v in kwargs.items()]
    return "|".join(args_str_list + kwargs_str_list)


def get_variant_id(record: pysam.VariantRecord) -> str:
    """
    Return a unique variant id based on chr/pos/ref/alt + SV specific INFO fields if any

    >>> get_variant_id(pysam.VariantRecord(chrom='10', pos=94077, ref='A', alts=['C']))
    "10:94077:A:C"
    """
    base = [record.chrom, str(record.pos), record.ref, ",".join(list(record.alts))]

    # INFO keys reserved to identify structural variants (VCF 4.4 specs)
    sv_keys = [
        "IMPRECISE",
        "NOVEL",
        "END",
        "LEN",
        "SVLEN",
        "SVTYPE",
        "CIPOS",
        "CIEND",
        "HOMLEN",
        "HOMSEQ",
        "BKPTID",
        "MEINFO",
        "METRANS",
    ]
    for k in sv_keys:
        try:
            data = record.info.get(k, None)
        except ValueError:
            # k is not in record (returns a ValueError: Invalid header)
            data = None
        if data:
            base.append(f"{k}={data}")

    return ":".join(base)


def get_db_key(
    record: pysam.VariantRecord,
    ann: str,
    dist_var: int | list[int],
    mask: int | list[int],
) -> str:
    return stringify_args(get_variant_id(record), ann, dist_var, mask)


class CacheDB:
    def __init__(
        self, host: str, port: int = 6379, password: str = "", db: int = 0
    ) -> None:
        if password != "":
            self.conn = redis.Redis(host, port, db, password)
        else:
            self.conn = redis.Redis(host, port, db)

    def set(self, key: str, value: str | dict | list) -> None:
        self.conn.set(key, json.dumps(value))

    def get(self, key: str) -> None | str | dict | list:
        res = self.conn.get(key)
        if res:
            return json.loads(res)
        return None

    def invalidate(self, key: str) -> None:
        raise NotImplementedError()

    def invalidate_all(self) -> None:
        raise NotImplementedError()
