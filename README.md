# Philips TV Remote

A Home Assistant custom integration that controls Philips TVs over the local
JointSpace API. It gives you a media player, a remote, and an Ambilight style
selector, and it pairs with the TV using the on-screen PIN.

The integration polls the TV on your local network. It sends nothing to the
cloud.

## Supported TVs

This integration targets Philips Android TV and Google TV models that expose
JointSpace API v6 over HTTPS on port 1926 and pair with `digest_auth_pairing`.
The Philips 65OLED706/96 is the reference model.

Older models that use an unsecured JointSpace API (HTTP on port 1925, no
pairing) are not the focus here, though the config flow creates an entry for
any v6 TV it reaches.

The protocol work is done by the [`ha-philipsjs`](https://pypi.org/project/ha-philipsjs/)
library, which Home Assistant installs automatically.

## Install through HACS

1. In HACS, open the three-dot menu and choose **Custom repositories**.
2. Add `https://github.com/cherub0526/philips-tv-remote` with the category
   **Integration**.
3. Search HACS for **Philips TV Remote** and install it.
4. Restart Home Assistant.

## Add your TV

1. Go to **Settings** > **Devices & services** > **Add integration**.
2. Search for **Philips TV Remote**.
3. Enter the TV's IP address. Optionally enter its MAC address to enable
   Wake-on-LAN.
4. A PIN appears on the TV screen. Type that PIN into Home Assistant.

Home Assistant stores the credentials the pairing returns. If the TV ever
rejects them, remove the integration and add it again to pair with a fresh
PIN.

## Entities

The integration adds one device with three entities.

### Media player

Controls power, volume, mute, source selection, and playback. Source
selection lists the apps installed on the TV, and falls back to the TV's
hardware inputs. Playback controls map to the TV's transport keys.

Turning the media player on sends a Wake-on-LAN magic packet first, when you
configured a MAC address, then asks the TV to power on.

### Remote

Sends raw remote-control keys. Call `remote.send_command` with one or more of
these key names.

```
Standby, Back, Find, RedColour, GreenColour, YellowColour, BlueColour, Home,
VolumeUp, VolumeDown, Mute, Options, Dot, Digit0, Digit1, Digit2, Digit3,
Digit4, Digit5, Digit6, Digit7, Digit8, Digit9, Info, CursorUp, CursorDown,
CursorLeft, CursorRight, Confirm, Next, Previous, Adjust, WatchTV, Viewmode,
Teletext, Subtitle, ChannelStepUp, ChannelStepDown, Source, AmbilightOnOff,
PlayPause, Pause, Play, FastForward, Stop, Rewind, Record, Online
```

### Ambilight

A `select` named Ambilight that sets the TV's Ambilight style in one step. Its
options come from the styles the TV reports, grouped into these families.

- `Off` turns Ambilight off.
- Follow Video presets, such as `Follow Video: Standard` and
  `Follow Video: Game`.
- Follow Audio presets, such as `Follow Audio: VU Meter`.
- Follow Color presets, such as `Follow Color: Hot Lava`.
- `Lounge` for the lounge-light style.
- `Game 1` through `Game 5` for the game-bar styles.

The integration adds this entity only when the TV reports more than the bare
Off style, so the TV must be on when you first set it up for Ambilight to
appear.

Apple Home does not show `select` entities, so you control Ambilight from Home
Assistant. To reach it from HomeKit, wrap a style in a Home Assistant scene and
expose that scene. The media player does appear in Apple Home, as a single
Television accessory, because it now carries the TV device class.

## Wake-on-LAN

Enter the TV's MAC address during setup to let Home Assistant wake the TV from
a full power-off. Without a MAC address, Home Assistant can still power the TV
on from standby, but not from off. Wake-on-LAN also needs the TV's own setting
enabled, and the magic packet must be able to reach the TV's network segment.

## Security and privacy

The TV presents a self-signed certificate, so the underlying `ha-philipsjs`
library turns off TLS verification. The traffic is still encrypted, but a
man-in-the-middle on the same local network can present their own certificate
and intercept or alter the control traffic.

Home Assistant stores the pairing credentials, the device ID and auth key, in
its config storage. Anyone who reads that storage holds credentials that
control this TV on the local network.
