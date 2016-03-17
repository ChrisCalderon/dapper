from . import serpent
from . import ipcrpc
from . import httprpc
from typing import Optional, Union, Tuple

IPC = "IPC"
HTTP = "HTTP"

ConnectInfoType = Union[str,Tuple[str]]
class Contract:
    def __init__(self, code: str, backend: str = IPC, connect_info: Optional[]):
        if backend == IPC:
            self.rpc = ipcrpc.RPC
