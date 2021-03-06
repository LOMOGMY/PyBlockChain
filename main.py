# title           :main.py
# description     :The console interface and main program of the blockchain based on flask.
# author          :CharlesYang
# created         :20180421
# version         :0.0.5
# usage           :python3 main.py
# notes           :
# python_version  :3.6.4
# ==============================================================================
"""
Web interact with the BlockChain
"""
from flask import Flask, jsonify, request
from uuid import uuid4
from Chain import BlockChain
import configparser as cp
import os
import logging
import sys

config = cp.ConfigParser()
app = Flask(__name__)
# ID of the miner/user.
node_identifier = '-1'
# Initialize the main blockchain.
MainChain = BlockChain()
logger = logging.getLogger('BlockChain')
logger.setLevel(logging.INFO)
fileLogHandler = logging.FileHandler('blockchain.log')
logger.addHandler(fileLogHandler)
# logger.addHandler(logging.StreamHandler(sys.stdout))


def config_init():
    """
    Initialize the config file.
    :return: None
    """
    # Create config sections and default settings.
    config.add_section('api')
    config.set('api', 'bind_ip', '0.0.0.0')
    config.set('api', 'port', '5000')
    config.add_section('identity')
    user_uuid = str(uuid4()).replace('-', '')
    logger.info('User uuid: ' + user_uuid)
    config.set('identity', 'uuid', user_uuid)
    config.add_section('data')
    config.set('data', 'chain_dir', 'chain_data')
    config.write(open('config.ini', 'w'))
    logger.info('First run config generated.')


@app.route('/nodes', methods=['GET'])
def nodes_list():
    """
    Show the list of registered nodes.
    :return: The json type of the nodes data.
    """
    response = {
        'nodes': [node for node in MainChain.nodes],
        'length': len(MainChain.nodes),
    }
    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    """
    Read the full chain data.
    :return: The json type of the chain data.
    """
    response = {
        'chain': MainChain.chain,
        'length': len(MainChain.chain),
    }
    return jsonify(response), 200


@app.route('/mine', methods=['GET'])
def mine():
    """
    Main in the blockchain.
    :return: Information about the mined data.
    """
    last_block = MainChain.last_block
    last_proof = last_block['proof']
    proof = MainChain.proof_of_work(last_proof)
    # The sender of mined transaction is 0.
    MainChain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    block = MainChain.new_block(proof)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    """
    Start a new Transaction.
    data = {
        sender: Send of the transaction.
        recipient: Recipient of the transaction.
        amount: Amount to transfer.
    }
    :return: The result of the transaction.
    """
    values = request.get_json()

    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400
    if 'message' in values:
        index = MainChain.new_transaction(values['sender'], values['recipient'], values['amount'], values['message'])
    else:
        index = MainChain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    """
    Register a node in the network.
    data = {
        nodes:[list of the node]
    }
    :return: The result of the registration.
    """
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        MainChain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(MainChain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    """
    Consensus system check.
    :return: The status of the present chain.
    """
    replaced = MainChain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': MainChain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': MainChain.chain
        }

    return jsonify(response), 200


@app.route('/save', methods=['GET'])
def save_blocks():
    response = {
        'message': 'Chain state saved',
        'changed_block': MainChain.save_blocks(data_path)
    }
    return jsonify(response), 200


if __name__ == '__main__':
    # Judge if config is missing.
    logger.info('Welcome to blockchain project.')
    if not os.path.exists('config.ini'):
        logging.warning('Config file not found, setup for the first run.')
        config_init()
    # Read the config file.
    config.read('config.ini')
    # Create data dir.
    data_path = config.get('data', 'chain_dir')
    if not os.path.exists(data_path):
        logger.warning('Data path not found, setup for the first run.')
        os.makedirs(data_path)
        logger.info('Will loading blocks.')
    MainChain.load_blocks(data_path)
    logger.info('Will complete self registration.')
    api_url = 'http://' + config.get('api', 'bind_ip') + ':' + str(config.getint('api', 'port'))
    MainChain.register_node(api_url)
    node_identifier = config.get('identity', 'uuid')
    """
    Run the main app.
    """
    logger.info('Now the API is open in ' + api_url)
    app.run(host=config.get('api', 'bind_ip'), port=config.getint('api', 'port'))
