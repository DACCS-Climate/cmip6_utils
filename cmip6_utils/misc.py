import hashlib


class BC:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    @classmethod
    def okgreen(cls, s: str) -> str:
        return cls.OKGREEN + s + cls.ENDC

    @classmethod
    def fail(cls, s: str) -> str:
        return cls.FAIL + s + cls.ENDC

    @classmethod
    def warn(cls, s: str) -> str:
        return cls.WARNING + s + cls.ENDC

    @classmethod
    def bold(cls, s: str) -> str:
        return cls.BOLD + s + cls.ENDC

    @classmethod
    def header(cls, s: str) -> str:
        return cls.HEADER + s + cls.ENDC


def verify_checksum(fname: str, refchecksum: str) -> bool:
    checksum = hashlib.sha256(open(fname, "rb").read()).hexdigest()
    return checksum == refchecksum
