from . import serpent
from . import ipcrpc
from . import httprpc
from typing import Union
from enum import Enum

Backend = Enum("Backend", "ipc http")
AddressType = Union[ipcrpc.AddressType,
                    httprpc.AddressType,
                    None]


class ContractError(Exception):
    pass


class Contract:
    def __init__(self,
                 code: str,
                 verbose: bool = False,
                 backend: Backend = Backend.ipc,
                 address: AddressType = None):

        if backend == Backend.ipc:
            RpcClient = ipcrpc.RpcClient
        elif backend == Backend.http:
            RpcClient = httprpc.RpcClient
        else:
            err = "Invalid backend choice: {}; choose Backend.ipc or Backend.http"
            raise ContractError(err.format(backend))

        if address is None:
            try:
                self.rpc = RpcClient(verbose=verbose)
            except Exception:
                raise ContractError("Couldn't connect to default for {}.".format(backend))
        else:
            try:
                self.rpc = RpcClient(address=address, verbose=verbose)
            except Exception as exc:
                raise ContractError("Error setting up RPCCLient with address {}: {}".format(address))

        self.signature = serpent.mk_full_signature(code, as_dict=True)
        self._generate_funcs()

    def _generate_funcs(self):
        for item in self.signature:
            if item["type"] == "function":
                pass