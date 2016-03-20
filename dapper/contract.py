from . import serpent
from . import ipcrpc
from . import httprpc
from typing import Optional, Union, Tuple
from enum import Enum

Backend = Enum("Backend", "ipc http")
AddressType = Optional[Union[str,Tuple[str,int]]]
class ContractError(Exception): pass


class Contract:
    def __init__(self,
                 code: str,
                 verbose: bool = False,
                 backend: Backend = Backend.ipc,
                 address: AddressType = None):

        if backend == Backend.ipc:
            RPCClient = ipcrpc.RpcClient
        elif backend == Backend.http:
            RPCClient = httprpc.RPCClient
        else:
            raise ContractError("Invalid backend choice: {}; choose IPC or HTTP".format(backend))

        if address is None:
            try:
                self.rpc = RPCClient(verbose=verbose)
            except Exception:
                raise ContractError("Couldn't connect to default for {}.".format(backend))
        else:
            try:
                self.rpc = RPCClient(address=address, verbose=verbose)
            except Exception as exc:
                raise ContractError("Error setting up RPCCLient with address {}: {}".format(address))
