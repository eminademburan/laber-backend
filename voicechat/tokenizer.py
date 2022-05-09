#! /usr/bin/python
# ! -*- coding: utf-8 -*-

import sys
import os
import time
from random import randint

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from voicechat.src.RtcTokenBuilder import RtcTokenBuilder, Role_Attendee

appID = "c1d043e419a6463f8c8775b42807aba7"
appCertificate = "6dab7fbb14144a0d8be182e3ed4a91bf"
uid = 0
expireTimeInSeconds = 36000
currentTimestamp = int(time.time())
privilegeExpiredTs = currentTimestamp + expireTimeInSeconds

def generate_token(channelName):
    token = RtcTokenBuilder.buildTokenWithUid(appID, appCertificate, channelName, uid, Role_Attendee,
                                              privilegeExpiredTs)
    return token
