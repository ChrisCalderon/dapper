from . import ipcrpc
from . import httprpc
from .rpc_client_base import JsonBatch
from typing import Union, List, Tuple, Optional
from enum import Enum
import math
import sha3

Backend = Enum("Backend", "ipc http")
AddressType = Union[ipcrpc.AddressType,
                    httprpc.AddressType,
                    None]
PythonAbiAnalogs = Tuple[Union[int,str,bytes,List[int], Tuple[int, ...]], ...]


class ContractError(Exception):
    pass

class Contract:
    def __init__(self, *,
                 contract_address: str,
                 signature: JsonBatch,
                 backend: Backend=Backend.ipc,
                 rpc_address: AddressType=None,
                 sender_address: Optional[str]=None,
                 default_gas: int=int(math.pi*1e6),
                 verbose: bool=False):
        self._setup_rpc(backend, rpc_address, verbose)
        self.default_gas = hex(default_gas).strip("L")
        if sender_address is not None:
            self.sender_address = sender_address
        else:
            sender_address = self.rpc.eth_coinbase().get("result", False)
            if sender_address:
                self.sender_address = sender_address
        self.contract_address = contract_address
        self.signature = signature

    def _setup_rpc(self, backend: Backend, rpc_address: AddressType, verbose: bool):
        """Creates the rpc client using the appropriate backend."""
        if backend == Backend.ipc:
            RpcClient = ipcrpc.RpcClient
        elif backend == Backend.http:
            RpcClient = httprpc.RpcClient
        else:
            err = "Invalid backend choice: {}; choose Backend.ipc or Backend.http"
            raise ContractError(err.format(backend))

        if rpc_address is None:
            try:
                self.rpc = RpcClient(verbose=verbose)
            except Exception:
                raise ContractError("Couldn't connect to default for {}.".format(backend))
        else:
            try:
                self.rpc = RpcClient(address=rpc_address, verbose=verbose)
            except Exception as exc:
                err = "Error setting up RPCCLient; type={}; address={}; exc={}"
                raise ContractError(err.format(backend, rpc_address, exc))


