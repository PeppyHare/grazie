#!/usr/bin/env python
"""
Authors: Evan Bluhm (https://github.com/PeppyHare)
"""

import argparse
import json
import logging
import os
import random
import sys
import time
import urllib

import nltk
from slackclient import SlackClient

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def try_load_env_var(var_name):
    """Read environment variables into a configuration object

    Args:
        var_name (str): Environment variable name to attempt to read
    """
    value = None
    if var_name in os.environ:
        value = os.environ[var_name]
    else:
        logging.info(
            "Environment variable %s is not set. Will try to read from command-line",
            var_name)
    return value


class DogBot(object):
    """
    This gives you dogs. You happy now.
    """
    def __init__(self, slack_token, giphy_api_key):
        self._bot_id = 'B6CL37JBH'
        self.read_websocket_delay = 1  # 1 second delay between reading from firehose
        self.slack_client = SlackClient(slack_token)
        self.giphy_api_key = giphy_api_key
        self.default_terms = ['dog', 'pug', 'whippet', 'greyhound', 'boye']


    def listen(self):
        """
        Listen to the slack events firehose and wait for messages to come in
        """
        slack_client = self.slack_client
        if slack_client.rtm_connect():
            logging.info("Slack bot connected and running!")
            while True:
                event = parse_slack_output(slack_client.rtm_read())
                if event:
                    logging.info("event received from slack: %s",
                                 event.get('text'))
                    if 'bot_id' in event.keys():
                        logging.info("We shouldn't be talking to bots!!")
                        continue
                    else:
                        self.respond_to_message(event)
                time.sleep(self.read_websocket_delay)
        else:
            logging.error("Connection failed. Invalid Slack token or bot ID?")


    def respond_to_message(self, event):
        """
        Construct and send the appropriate response back to the Slack channel
        """
        search_terms = [random.choice(self.default_terms)]
        # Tag the parts of speech in event['text'] according to the Penn Treebank tagset
        pos_tags = nltk.pos_tag(nltk.word_tokenize(event['text']))
        logging.debug("Tokenization of message: %s", pos_tags)
        nouns = []
        noun_tags = ['NN', 'NNS', 'NNP', 'NNPS']
        verbs = []
        verb_tags = ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']
        adjectives = []
        adjective_tags = ['JJ', 'JJR', 'JJS']
        # send search terms in order [adjectives, nouns, verbs]
        for pos in pos_tags:
            if pos[1] in noun_tags:
                nouns.append(pos[0])
            if pos[1] in verb_tags:
                verbs.append(pos[0])
            if pos[1] in adjective_tags:
                adjectives.append(pos[0])
        search_terms = search_terms + adjectives + nouns + verbs
        channel = event['channel']
        logging.debug("search_terms: %s", search_terms)
        gif_link = find_gif(self.giphy_api_key, search_terms)
        logging.info(gif_link)
        self.slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=gif_link)


def parse_slack_output(slack_rtm_output):
    """
    The Slack Real Time Messaging API is an events firehose. This parsing
    function returns the last-seen message if there is one, otherwise returns
    None
    """
    output_list = slack_rtm_output
    for output in output_list:
        # We are a creepy bot, we listen to everything you say
        if output and 'text' in output:
            return output
    return None


def find_gif(giphy_api_key, search_terms):
    """
    Find the perfect gif for any situation
    """
    api_endpoint = 'http://api.giphy.com/v1/gifs/search?'
    giphy_search_params = ['api_key=%s' % giphy_api_key]
    giphy_search_params.append('q=' + '+'.join(search_terms))
    giphy_search_params.append('limit=1')
    giphy_search_params.append('rating=r')
    request = api_endpoint + '&'.join(giphy_search_params)
    logging.debug("request to send: %s", request)
    response = json.loads(urllib.urlopen(request).read())
    logging.debug("giphy response: %s", response)
    if 'data' not in response.keys():
        logging.error("We didn't get back anything from giphy!")
        return None
    return response['data'][0]['images']['downsized']['url']


def main():
    """
    The main thing
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--giphy-apikey",
        dest="GIPHY_API_KEY",
        help="Giphy app API key (free)",
        type=str,
        required=False,
        default=try_load_env_var("GIPHY_API_KEY"))
    parser.add_argument(
        "--slack-token",
        dest="SLACK_TOKEN",
        help="Slack client token",
        type=str,
        required=False,
        default=try_load_env_var("SLACK_TOKEN"))
    args = parser.parse_args()
    if not (args.GIPHY_API_KEY and args.SLACK_TOKEN):
        parser.print_help()
        sys.exit(1)

    dogbot = DogBot(
        slack_token=args.SLACK_TOKEN,
        giphy_api_key=args.GIPHY_API_KEY)
    dogbot.listen()

if __name__ == "__main__":
    main()
