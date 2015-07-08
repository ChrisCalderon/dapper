def main(*args):
    print '''\
Usage: dapper <command> [<arg> ...]

Commands:
  help             Shows this help message.
  compile          Compiles code in a project.
  call             Calls a function in a compiled contract.
  send             Sends a transaction interacting with a contract.
  run-tests        Runs tests for the project using a simulated network.
  get-sigs         Outputs addresses and signatures for contracts.
  new-dapp         Sets up a new dapp directory.
  raw-rpc          CLI for using JSON RPC with your local ethereum node.

Use 'dapper <command> help' to see more detailed help for each command.
'''
