# JigasiRecepta

Incoming SIP call router for `Jigasi`.

This repository contains scripts, files and documentation to convert
`FreeSwitch` into a router for incoming SIP calls for `Jigasi`. Assumed that
following services are already installed and configured correctly:

- `Jitsi`
- `Jigasi`
- `FreeSwitch`

## Adding JigasiRecepta

`JigasiRecepta` is a plugin for `FreeSwitch` to route incoming SIP calls to
`Jigasi`. The following steps are tested in `Debian 12 Bookworm`. Assumed
that `FreeSwitch` already installed and running on this server.

### Install additional packages

```bash
apt-get update
apt-get install python3 python3-requests
```

### Enable Python3 in FreeSwitch

In _/etc/freeswitch/autoload_configs/modules.conf.xml_:

```xml
<load module="mod_python3"/>
```

### Install JigasiRecepta

```bash
cd /usr/local/lib/python3.11/dist-packages
mkdir nordeck
cd nordeck
touch __init__.py
wget https://raw.githubusercontent.com/nordeck/jigasi-recepta/main/files/jigasi.py
```

### DialPlan

```bash
cd /etc/freeswitch/dialplan/public
wget https://raw.githubusercontent.com/nordeck/jigasi-recepta/main/files/98_public_jigasi_dialplan.xml

cd /etc/freeswitch/dialplan/default
wget https://github.com/nordeck/jigasi-recepta/blob/main/files/99_default_jigasi_dialplan.xml
```

### Directory

```bash
cd /etc/freeswitch/directory/default
wget https://raw.githubusercontent.com/nordeck/jigasi-recepta/main/files/jigasi.xml
```

Update `jigasiPassword` in this file according to your settings.

### Global variables

Put the following variable into _/etc/freeswitch/vars.xml_:

```xml
<X-PRE-PROCESS cmd="set" data="conference_mapper_jigasi_uri=https://domain/path?pin={pin}"/>
```

Update `conference_mapper_jigasi_uri` according to your conference mapper URI.

### Restart

Restart the service:

```bash
systemctl restart freeswitch
```

## Usage

Call the external number set in
[98_public_jigasi_dialplan.xml](files/98_public_jigasi_dialplan.xml).
e.g.:

```
jigasi@freeswitch_address:5080
```

Or call the internal number set in
[99_default_jigasi_dialplan.xml](files/99_default_jigasi_dialplan.xml).
e.g.:

```
jigasi
```

Type PIN when asked.

## Tips

### DNS records

If you have a domain name, set `SRV` records for SIP service.

- DNS `A` record for `sip.mydomain.com` which points the IP address of this
  server.

- DNS `SRV` record for `_sip._tcp.mydomain.com` which points `sip.mydomain.com`.
  Select `5080` as port if you still use the default external port.

- DNS `SRV` record for `_sip._udp.mydomain.com` which points `sip.mydomain.com`.
  Select `5080` as port if you still use the default external port.

In this case, the remote peer can call `jigasi@mydomain.com` without setting the
port.

You may check the records in [VoIP Toolbox](https://voiptoolbox.net). Write your
domain into the input box. e.g `mydomain.com`
