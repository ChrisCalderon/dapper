"""Calls the C++ serpent binary."""
import subprocess
import ujson
from typing import Union


class SerpentError(Exception):
    def __init__(self, msg, exc):
        super().__init__(exc.returncode, exc.cmd, exc.output)
        self.message = message
        
    def __str__(self):
        return "{} : {}".format(self.message, super().__str__())


def call_serpent(command: str, code: str, err_msg: str) -> str:
    try:
        return subprocess.check_output(["serpent", command, code],
                                       universal_newlines=True)
    except subprocess.CalledProcessError as exc:
        raise SerpentError(err_msg, exc)
                                    

def compile(code: str) -> str:
    return call_serpent("compile", code, "compiler error")


def mk_full_signature(code: str, as_dict: str=False) -> Union[str,dict]:
    output = call_serpent("mk_full_signature", code, "contract signature error")
    if as_dict:
        return ujson.decode(output)
    return output
