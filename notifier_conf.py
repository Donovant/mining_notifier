'''
	This script serves to obtain and/or set variables needed for the notifier system.
    Author: Donovan Torgerson
    Email: Donovan@Torgersonlabs.com
'''
from os import getenv

class config:
	text_source = getenv('text_source', None)
	text_consumer = getenv('text_consumer', None)
	miner_ip = getenv('miner_ip', '192.168.1.195')
	miner_port = getenv('miner_port', '4028')
	twilio_id = getenv('twilio_id', None)
	twilio_token = getenv('twilio_token', None)
