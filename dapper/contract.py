from . import ipcrpc
from . import httprpc
from .rpc_client_base import JsonBatch
from typing import Union, List, Tuple, Optional, NamedTuple
from enum import Enum
from .abi_encode import get_python_type
from sha3 import sha3_256 as keccak256  # pre-NIST sha3 standard
from collections import defaultdict, namedtuple
import math

Backend = Enum("Backend", "ipc http")
AddressType = Union[ipcrpc.IpcAddress,
                    httprpc.HttpAddress,
                    None]


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
            else:
                raise ContractError('Unable to detect default sender address')
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
                err = "Couldn't connect to default for {}."
                raise ContractError(err.format(backend))
        else:
            try:
                self.rpc = RpcClient(address=rpc_address, verbose=verbose)
            except Exception as exc:
                err = "Error setting up RpcClient; type={}; address={}; exc={}"
                raise ContractError(err.format(backend, rpc_address, exc))

    def _generate_contract_functions(self):
        function_names = defaultdict(lambda: defaultdict(list))
        function_info = namedtuple('function_info', 'prefix abi_types')
        for item in self.signature:
            if item['type'] == 'function':
                name, types = item['name'].split('(')
                abi_types = types.rstrip(')').split(',')
                py_types = tuple(map(get_python_type, abi_types))
                if item['name'] not in function_names:
                    function_names[name] = {}
                if py_types not in function_names[name]:
                    function_names[name][py_types] = []
                prefix = keccak256(item['name'].encode('utf8')).hexdigest()
                function_names[name][py_types].append((prefix, abi_types))




