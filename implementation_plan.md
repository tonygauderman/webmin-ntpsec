# NTPsec Webmin Module for TurnKey Linux

This plan details the design and implementation of a custom Webmin module to configure, monitor, and manage the `ntpsec` daemon on a TurnKey Linux (Debian-based) distribution. Since the module will run on another computer, this plan also includes questions for the user to retrieve system status and config files from that machine to ensure seamless compatibility.

## User Review Required

> [!IMPORTANT]
> The Webmin module will use standard Webmin UI library functions (`ui-lib.pl`) to ensure it styles properly with modern Webmin themes, particularly the Authentic Theme used by TurnKey Linux.
> We will also generate a `.wbm.gz` (Webmin module package) build script. This will allow you to package the files and install the module directly from the Webmin UI ("Webmin" -> "Webmin Configuration" -> "Webmin Modules").

## Open Questions

To help make the parser and status checks 100% accurate for your target machine, please run the following commands on your TurnKey Linux system and share the outputs:

1. **Active service name:** What is the output of:
   ```bash
   systemctl list-units --type=service | grep -E 'ntp|chrony'
   ```
2. **Current NTPsec Configuration:** Please provide the contents of `/etc/ntp.conf` (or `/etc/ntpd.conf` if that is used instead).
3. **NTP Peers Output:** What is the output of the peer status query?
   ```bash
   ntpq -p
   ```
4. **NTS Diagnostics Output:** What is the output of the experimental NTS client check?
   ```bash
   ntpq -c ntsinfo
   ```

## Proposed Changes

All files will be created under the repository root `/Users/tonygauderman/Antigravity/webmin-ntpsec`.

---

### Module Definition and Config

These files register the module inside Webmin and specify default settings.

#### [NEW] [module.info](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/module.info)
Defines metadata, name, category ("system"), supported OSes (`*-linux`), and version.

#### [NEW] [config](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/config)
Defines the module default configuration variables:
- `ntp_conf=/etc/ntp.conf` (path to config)
- `ntp_service=ntp` (or `ntpsec`, dynamically adjusted)
- `ntpq_path=/usr/bin/ntpq`
- `ntpdig_path=/usr/bin/ntpdig`

#### [NEW] [config.info](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/config.info)
Provides metadata for editing module configuration inside Webmin.

#### [NEW] [lang/en](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/lang/en)
English language keys and UI strings for tables, labels, form descriptions, and messages.

---

### Core Helper Library

#### [NEW] [ntpsec-lib.pl](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/ntpsec-lib.pl)
Perl library containing backend functions:
- `get_ntp_config()`: Parses `/etc/ntp.conf` into structured hashes (servers, pools, restrict rules, driftfile, etc.).
- `save_ntp_config(config_ref)`: Serializes structured hashes back to `/etc/ntp.conf`, preserving comments where possible.
- `get_ntpq_peers()`: Executes `ntpq -p` and returns parsed peers with their synchronization indicators (`*`, `+`, etc.).
- `get_ntp_status()`: Checks whether the systemd service is active/running and enabled at boot.
- `manual_sync()`: Stops NTPsec, runs `ntpdig -u` (or `ntpd -gq`) to sync immediately, and restarts NTPsec.

---

### Web UI Pages (CGI Scripts)

These scripts handle the Webmin visual representation using standard `ui-lib.pl`.

#### [NEW] [index.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/index.cgi)
The dashboard/main page:
- Visual service status (running/stopped, boot enable/disable buttons).
- Manual sync action button.
- A table listing active NTP peers from `ntpq -p` (Remote Server, RefID, Stratum, Type, When, Poll, Reach, Delay, Offset, Jitter).
- Navigation links/buttons to other configure sub-pages.

#### [NEW] [edit_servers.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/edit_servers.cgi)
Lists all parsed `server`, `pool`, and `peer` directives. Includes a form to add a new server/pool/peer with options:
- Hostname/IP address
- Type (`server`, `pool`, `peer`)
- Options: `iburst`, `prefer`, `nts` (Network Time Security), `minpoll`, `maxpoll`, etc.

#### [NEW] [save_server.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/save_server.cgi)
Saves or updates a time source in the configuration file.

#### [NEW] [delete_servers.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/delete_servers.cgi)
Bulk deletes selected time sources.

#### [NEW] [edit_restrict.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/edit_restrict.cgi)
Lists current client access control (`restrict`) rules. Includes a form to add rules specifying address/default/mask and flags like `kod`, `nomimic`, `nomodify`, `noquery`, `nopeer`, `noserve`, `notrap`.

#### [NEW] [save_restrict.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/save_restrict.cgi)
Saves/updates a restrict rule.

#### [NEW] [delete_restricts.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/delete_restricts.cgi)
Bulk deletes selected restrict rules.

#### [NEW] [edit_misc.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/edit_misc.cgi)
Form to configure miscellaneous settings:
- Driftfile path
- Logfile path
- Statistics directory (`statsdir`)
- Tinker panic threshold (e.g. disable panic threshold via `tinker panic 0` to prevent daemon exit on large offsets).

#### [NEW] [save_misc.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/save_misc.cgi)
Saves miscellaneous settings.

#### [NEW] [edit_manual.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/edit_manual.cgi)
Provides a rich textarea to manually edit `/etc/ntp.conf` for advanced options.

#### [NEW] [save_manual.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/save_manual.cgi)
Validates and saves the manual text back to `/etc/ntp.conf`.

#### [NEW] [action.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/action.cgi)
Starts, stops, or restarts the `ntpsec` systemd service, and handles enabling/disabling at boot.

#### [NEW] [sync.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/sync.cgi)
Executes manual time synchronization. Shows output in real time.

---

### Packaging and Asset Scripts

#### [NEW] [build.py](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/build.py)
A helper python script to package all module files into a standard Webmin distribution file `ntpsec.wbm.gz`.

#### [NEW] [images/icon.svg](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/images/icon.svg)
A modern, vector SVG icon representing NTPsec (clock combined with shield/lock).

## Verification Plan

### Automated Tests
Since the module is written in Perl for a Webmin environment, we will verify correctness using:
- Syntax check command on all `.cgi` and `.pl` scripts:
  ```bash
  perl -cw <script_name>
  ```
- Mock test of the configuration parser: we will create a unit test script `test_parser.pl` that feeds mock `/etc/ntp.conf` inputs, parses them, serializes them, and asserts consistency.

### Manual Verification
1. Run the `build.py` script to generate `ntpsec.wbm.gz`.
2. Transfer the `.wbm.gz` file to the TurnKey Linux system.
3. Install the module through the Webmin UI: Webmin Configuration -> Webmin Modules -> From uploaded file.
4. Open the module and verify:
   - Dashboard loads and displays peers correctly.
   - Adding/removing servers parses and updates `/etc/ntp.conf` as expected.
   - Systemd start/stop/restart/enable actions function correctly.
   - Manual synchronization runs and outputs results.
