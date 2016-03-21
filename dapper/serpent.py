"""Calls the C++ serpent binary."""
from subprocess import CalledProcessError, check_output
import ujson
from typing import Union


class SerpentError(Exception):
    def __init__(self, message: str, exc: CalledProcessError):
        super().__init__(exc.returncode, exc.cmd, exc.output)
        self.message = message
        
    def __str__(self) -> str:
        return "{} : {}".format(self.message, super().__str__())


def call_serpent(command: str, code: str, err_msg: str) -> str:
    try:
        return check_output(["serpent", command, code],
                            universal_newlines=True)
    except CalledProcessError as exc:
        raise SerpentError(err_msg, exc)
                                    

def compile(code: str) -> str:
    return call_serpent("compile", code, "compiler error")


def mk_full_signature(code: str, as_dict: bool=False) -> Union[str,dict]:
    output = call_serpent("mk_full_signature", code, "contract signature error")
    if as_dict:
        return ujson.decode(output)
    return output