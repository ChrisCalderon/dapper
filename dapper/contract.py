from . import serpent
from . import ipcrpc
from . import httprpc
from .rpc_client_base import JsonBatch
from typing import Union, List, Tuple, Optional
from enum import Enum
import math
import sha3
from collections import defaultdict

Backend = Enum("Backend", "ipc http")
AddressType = Union[ipcrpc.AddressType,
                    httprpc.AddressType,
                    None]
PythonAbiAnalogs = Tuple[Union[int,str,bytes,List[int], Tuple[int, ...]], ...]


class ContractError(Exception):
    pass


def abi_to_python_types(types: str) -> PythonAbiAnalogs:
    result = []
    for abi_type in types.strip('()').split(','):
        if '[' in abi_type:
            bracket_i = abi_type.find('[')
            if bracket_i + 2 == len(abi_type):
                result.append(List[int])
            else:
                length = int(abi_type[bracket_i:-1])
                ints = tuple(int for i in range(length))
                result.append(Tuple.__getitem__(ints))
        elif 'int' in abi_type or 'fixed' in abi_type or abi_type=='address':
            result.append(int)
        elif 'bytes' in abi_type:
            result.append(bytes)
        elif abi_type == 'string':
            result.append(str)
        else:
            raise ValueError("Bad type in signature: {}".format(abi_type))
    return tuple(result)


class Contract:
    def __init__(self, *,
                 code: Optional[str]=None,
                 contract_address: Optional[str]=None,
                 signature: Optional[JsonBatch]=None,
                 verbose: bool=False,
                 backend: Backend=Backend.ipc,
                 rpc_address: AddressType=None,
                 sender_address: Optional[str]=None,
                 default_gas: int=int(math.pi*1e6)):
        self.default_gas = hex(default_gas).strip("L")
        self._setup_rpc(backend, rpc_address)
        self._setup_address(sender_address)
        if code and (not signature) and (not contract_address):
            self._setup_code(code)
        elif signature and contract_address:
            self.signature = signature
            self.contract_address = contract_address

    def _setup_rpc(self, backend: Backend, rpc_address: AddressType):
        """Creates the rpc client using the appropriate backend."""
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
        """Gets the address via rpc if neccesary and saves it."""
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
        """Compiles/uploads code and stores the signature and address."""
        self.signature = serpent.mk_full_signature(code, True)
        self.compiled_code = serpent.compile(code)
        response = self.rpc.eth_sendTransaction({"from": self.coinbase,
                                                 "data": self.compiled_code,
                                                 "gas": self.default_gas})
        txhash = response.get("result")
        if txhash:
            while True:
                receipt = self.rpc.eth_getTransactionReceipt(txhash)["result"]
                if receipt:
                    self.contract_address = receipt["contractAddress"]
                    break

    def _generate_sig_info(self):
        """Stuffs signature info into convenient data structures."""
        self.functions = defaultdict(lambda: defaultdict(dict))
        self.events = defaultdict(lambda: defaultdict(dict))

        for item in self.signature:
            name = item["name"]
            prefix = sha3.sha3_256(name.encode("utf8"))
            types_start = name.find("(")
            python_name = name[:types_start]
            abi_types = name[types_start+1:-1].split(',')
            python_types = abi_to_python_types(abi_types)
            item_type = item["type"]
            if item_type == "function":
                info_holder = self.functions
            elif item_type == "event":
                info_holder = self.events
            else:
                raise ValueError("Bad type in contract signature: {}".format(item_type))

            if python_types in info_holder[python_name]:
                raise ValueError("Repeated {} signatures in contract signature!".format(item_type))

            info_holder[python_name][python_types]["prefix"] = prefix
            info_holder[python_name][python_types]["abiTypes"] = abi_types

