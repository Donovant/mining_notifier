'''
    This script serves to send text messages when miner temps reach or exceed 80 degrees celsius.
    Author: Donovan Torgerson
    Email: Donovan@Torgersonlabs.com
'''
# built-in imports
import logging
import json
import socket
import sys

# external imports
from twilio.rest import Client

# user defined imports
from notifier_conf import config
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')


def setup_logger(name, log_file, level=logging.INFO):
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

# general logger
log = setup_logger('logger', 'miner.log')

# data collection logger
data_logger = setup_logger('data_logger', 'miner_data.log')


def c_to_f_conversion(temp_in_celsius):
    return (temp_in_celsius * 9/5) + 32


def message():
    s9_ip = config.miner_ip
    s9_port = int(config.port_number)
    size = 4096

    twilio_id = config.twilio_id
    twilio_token = config.twilio_token
    if twilio_id == None:
        error = 'Valid twilio_id required. Messaging feature will not work.'
        log.error(error)
        print(error)
    if twilio_token == None:
        error = 'Valid twilio_token required. Messaging feature will not work.'
        log.error(error)
        print(error)

    text_source = config.text_source
    text_consumer = config.text_consumer
    if text_source == None:
        error = 'Valid text_source required. Messaging feature will not work.'
        log.error(error)
        print(error)
    if text_consumer == None:
        error = 'Valid text_consumer required. Messaging feature will not work.'
        log.error(error)
        print(error)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((s9_ip, s9_port))
        msg = json.dumps({'command': 'stats+summary'})
        sock.sendto(msg.encode(), (s9_ip, s9_port))
        response = ''
        while 1:
            chunk = sock.recv(size).decode("ascii").rstrip(' \t\r\n\0')
            if chunk:
                response += chunk
            else:
                break
        if '}{' in response:
            # For some reason the json returned from the api call is invalid. This should fix it.
            response = response.replace('}{', '},{')

        # Send shutdown so the socket closes the connection cleanly.
        sock.shutdown(socket.SHUT_RDWR)
        # close the socket.
        sock.close()
        # Decode the response.
        response_decoded = json.loads(response)
    except:
        error = sys.exc_info()[0]
        log.error(error)
        print(error)

    try:
        client = Client(twilio_id, auth_token)

        temp1 = response_decoded['stats'][0]['STATS'][1]['temp2_6']
        temp2 = response_decoded['stats'][0]['STATS'][1]['temp2_7']
        temp3 = response_decoded['stats'][0]['STATS'][1]['temp2_8']
        status1 = response_decoded['stats'][0]['STATS'][1]['chain_acs6']
        status2 = response_decoded['stats'][0]['STATS'][1]['chain_acs7']
        status3 = response_decoded['stats'][0]['STATS'][1]['chain_acs8']
        rate1 = response_decoded['stats'][0]['STATS'][1]['chain_rate6']
        rate2 = response_decoded['stats'][0]['STATS'][1]['chain_rate7']
        rate3 = response_decoded['stats'][0]['STATS'][1]['chain_rate8']
        found_block = response_decoded['summary'][0]['SUMMARY'][0]['Found Blocks']
        avg_rate = response_decoded['summary'][0]['SUMMARY'][0]['GHS av']

        # Log data in hopes of seeing trends.
        # Can also be used to see what temps maximize hash speed.
        data = '{} {} {} {} {} {} {}'.format(
            str(temp1).ljust(3), str(rate1).ljust(8),
            str(temp2).ljust(3), str(rate2).ljust(8),
            str(temp3).ljust(3), str(rate3).ljust(8),
            str(avg_rate))
        data_logger.info(data)

        # Check for bad chips.
        for status in [status1.lower(), status2.lower(), status3.lower()]:
            if 'x' in status:
                ct = 0
                for chip in status:
                    if chip == 'x':
                        ct += 1
                if ct <= 1:
                    log.warning('Bad chip detected')
                else:
                    msg = 'Bad chips detected!!!'
                    log.critical(msg)
                    txt_msg = "{}\n".format(msg)
                    sent_message = client.messages \
                        .create(
                            body=txt_msg,
                            from_=text_source,
                            to=text_consumer
                        )
                    print(sent_message.sid)
                    log.info(sent_message.sid)
        # Check for overheating.
        if temp1 >= 80 \
        or temp2 >= 80 \
        or temp3 >= 80:
            # Send temperature twilio message
            txt_msg = ("Miner is too hot!\n"
                       "temp2_6: {}\u00B0 C ({}\u00B0 F)\n"
                       "temp2_7: {}\u00B0 C ({}\u00B0 F)\n"
                       "temp2_8: {}\u00B0 C ({}\u00B0 F)"
                      ).format(temp1, c_to_f_conversion(temp1), \
                               temp2, c_to_f_conversion(temp2), \
                               temp3, c_to_f_conversion(temp3)
                              )
            sent_message = client.messages \
                .create(
                    body=txt_msg,
                    from_=text_source,
                    to=text_consumer
                )
            print(sent_message.sid)
            log.info(sent_message.sid)
        # Check if we found a block.
        if found_block > 0:
            # log that we found it.
            msg = 'WE FOUND A BLOCK!!!!'
            log.info(msg)

    except: # Catch all errors.
        exc_type, exc_obj, exc_tb = sys.exc_info()
        error = '{}, Line {}'.format(exc_type, exc_tb.tb_lineno)
        log.error(error)
        print(error)


if __name__ == '__main__':
    message()
