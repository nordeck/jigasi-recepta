"""
This script is tested on Debian 12 Bookworm.
Required packages: python3 python3-requests

Enable python3 in /etc/freeswitch/autoload_configs/modules.conf.xml

  <load module="mod_python3"/>

Put this file into /usr/local/lib/python3.11/dist-packages/nordeck/

Create /usr/local/lib/python3.11/dist-packages/nordeck/__init__.py
  touch /usr/local/lib/python3.11/dist-packages/nordeck/__init__.py

Add /etc/freeswitch/directory/default/jigasi.xml

Add /etc/freeswitch/dialplan/public/98_public_jigasi_dialplan.xml

Add /etc/freeswitch/dialplan/default/99_default_jigasi_dialplan.xml

Add Jigasi's conference mapper URI in /etc/freeswitch/vars.xml

  <X-PRE-PROCESS cmd="set" data="conference_mapper_jigasi_uri=https://domain/path?pin={pin}"/>

Restart FreeSwitch
  systemctl restart freeswitch.service
"""

import freeswitch
import requests

PIN_MAX_LENGTH = 10
ALLOWED_ATTEMPTS = 3
REQUESTS_TIMEOUT = 10
PIN_INPUT_TIMEOUT = 20

# pylint: disable=bare-except

# ------------------------------------------------------------------------------
def query_conference(pin):
    """
    Get the conference data from API service by using PIN.
    """

    # Dont continue if there is no pin
    if pin == "":
        return None

    try:
        api = freeswitch.API()
        uri = api.executeString("global_getvar conference_mapper_jigasi_uri")
        uri = uri.format(pin=pin)
        res = requests.get(uri, timeout=REQUESTS_TIMEOUT)
        jdata = res.json()
        conference = jdata.get("conference")

        freeswitch.consoleLog("info", f"Jigasi Conference: {conference}")

        return conference
    except:
        pass

    return None

# ------------------------------------------------------------------------------
def get_conference(session):
    """
    Ask the caller for PIN and get the conference name from API service by using
    this PIN.
    """

    try:
        # Ask for PIN
        session.streamFile("conference/conf-pin.wav")

        i = 1
        while True:
            # get PIN
            pin = session.getDigits(PIN_MAX_LENGTH, "#", PIN_INPUT_TIMEOUT * 1000)
            freeswitch.consoleLog("debug", f"PIN NUMBER {i}: {pin}")

            # Completed if there is a valid reply from API service for this PIN
            conference = query_conference(pin)
            if conference:
                return conference

            # Dont continue if there are many failed attempts.
            i += 1
            if i > ALLOWED_ATTEMPTS:
                break

            # Ask again after the failed attempt.
            if pin:
                session.streamFile("conference/conf-bad-pin.wav")
            else:
                session.streamFile("conference/conf-pin.wav")
    except:
        pass

    return {}

# ------------------------------------------------------------------------------
def handler(session, _args):
    """
    Jigasi handler. This is the main entrypoint.
    """

    try:
        freeswitch.consoleLog("info", "Jigasi handler\n")

        # Answer the call
        session.answer()
        session.sleep(2000)

        # Get the conference name. Cancel the session if no conference name.
        # The conference PIN number will be asked during this process.
        conference = get_conference(session)
        if not conference:
            session.hangup()
            return

        # Request is accepted
        freeswitch.consoleLog("info", "the conference request is accepted\n")
        session.streamFile("conference/conf-conference_will_start_shortly.wav")
        session.sleep(3000)

        # Transfer the call to Jigasi extension
        extension = session.getVariable("destination_number")
        session.setVariable("sip_h_Jitsi-Conference-Room", conference)
        session.setVariable("sip_h_X-Room-Name", conference)
        session.transfer(extension, "XML", "default")
    except:
        pass
