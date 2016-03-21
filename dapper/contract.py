from . import serpent
from . import ipcrpc
from . import httprpc
from .rpc_client_base import JsonBatch
from typing import Union, List, Tuple, Optional
from enum import Enum

Backend = Enum("Backend", "ipc http")
AddressType = Union[ipcrpc.AddressType,
                    httprpc.AddressType,
                    None]
PythonAbiAnalogs = Tuple[Union[int,str,bytes,List[int]], ...]


class ContractError(Exception):
    pass

def abi_to_python_types(types: str) -> PythonAbiAnalogs:
    result = []
    for abi_type in types.strip('()').split(','):
        if 'int' in abi_type or 'fixed' in abi_type:
            if '[' in abi_type:
                result.append(List[int])
            else:
                result.append(int)


class Contract:
    def __init__(self, *,
                 code: Optional[str]=None,
                 contract_address: Optional[str]=None,
                 signature: Optional[JsonBatch]=None,
                 verbose: bool=False,
                 backend: Backend=Backend.ipc,
                 rpc_address: AddressType=None,
                 sender_address: Optional[str]=None):

        self._setup_rpc(backend, rpc_address)
        self._setup_address(sender_address)
        if code and (not signature) and (not contract_address):
            self._setup_code(code)

    def _setup_rpc(self, backend: Backend, rpc_address: AddressType):
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

    def _setup_address(self, sender_address: Optional[str]):
        if sender_address is None:
            coinbase_json = self.rpc.eth_coinbase()
            coinbase = coinbase_json.get("result", None)
            if coinbase:
                self.coinbase = coinbase
            else:
                err = "Got bad json for coinbase: {}"
                raise ContractError(err.format(ujson.encode(coinbase_json)))
        else:
            self.coinbase = address #TODO: add re check.

    def _setup_code(self, code: str):
        self.signature = serpent.mk_full_signature(code, True)
        self.compiled_code = serpent.compile(code)


    def _generate_functions(self):
        for item in self.signature:
            if item["type"] == "function":
                paramlist_start = item["name"].find("(")
                name = item["name"][:paramlist_start]
