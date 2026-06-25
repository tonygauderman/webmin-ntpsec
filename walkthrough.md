# Walkthrough: NTPsec Webmin Module

I have completed the implementation of the Webmin module to manage the `ntpsec` daemon on TurnKey Linux. Below is a summary of the components built, verification results, and instructions for installing and running the package on your target machine.

## Accomplishments

1. **Core Configuration Parser & Serializer (`ntpsec-lib.pl`)**:
   - Parses the NTPsec `/etc/ntpsec/ntp.conf` file line-by-line into structured memory blocks.
   - Preserves comments and line placements during edits.
   - Handles `server`, `pool`, and `peer` directives (along with suboptions like `nts`, `iburst`, `prefer`, `minpoll`, and `maxpoll`).
   - Parses `restrict` rules and their specific flags.
   - Monitors active peers using `ntpq -p` and retrieves local/remote NTS statistics via `ntpq -c ntsinfo`.
   - Controls starting, stopping, restarting, and enabling/disabling the `ntpsec.service` at boot via systemd.

2. **Web UI Pages (CGI Scripts)**:
   - [index.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/index.cgi): Main dashboard rendering service status, action buttons, module configuration area (placed right at the top for quick access), active peers table, NTS statistics, and the AJAX refresh control widget.
   - [status_ajax.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/status_ajax.cgi): A lightweight JSON API endpoint returning live daemon status, service controls, parsed peers, and NTS statistics.
   - [edit_servers.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/edit_servers.cgi), [save_server.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/save_server.cgi), [delete_servers.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/delete_servers.cgi): Complete CRUD interface for upstream NTP sources (servers/pools).
   - [edit_restrict.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/edit_restrict.cgi), [save_restrict.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/save_restrict.cgi), [delete_restricts.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/delete_restricts.cgi): CRUD interface for client access restriction filters.
   - [edit_misc.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/edit_misc.cgi), [save_misc.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/save_misc.cgi): Settings form for logs, driftfile, tinker panic, and local NTS server keys/certs.
   - [edit_manual.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/edit_manual.cgi), [save_manual.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/save_manual.cgi): Raw text editor for direct `/etc/ntpsec/ntp.conf` modifications.
   - [action.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/action.cgi): Central service boot/state processor.
   - [sync.cgi](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/sync.cgi): Halts the service, executes `ntpdig -S` using configured upstream hosts to step the clock immediately, prints output in real-time to the browser, and restarts the service.

3. **AJAX Real-Time Auto-Refresh**:
   - Added a **Refresh** button and an **Auto Refresh** dropdown selector (Off, 5s, 10s, 30s, 60s) to the dashboard.
   - Implemented Javascript fetch logic to query `status_ajax.cgi` and update status displays, action buttons, active peers tables, and NTS statistics dynamically in-place without page reloads.
   - Saves and retrieves the interval selection via browser `localStorage` to persist auto-refresh preferences across page reloads and browser sessions.

4. **Namespacing and Caching Resolution**:
   - Every CGI script is compiled at startup inside the `ntpsec` package when Webmin's miniserv caches scripts.
   - Added compile-time `use WebminCore;` declarations to **every CGI script** and **`ntpsec-lib.pl`**.
   - This ensures all Webmin core library subroutines (like `ui_print_header`) are correctly exported into the module's package namespace (`ntpsec`), completely resolving the `500 - Undefined subroutine` execution failure.

5. **Modern UI/UX Assets**:
   - [images/icon.svg](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/images/icon.svg): A modern, vector-graphic SVG icon representing NTPsec (clock combined with a shield and padlock theme).

6. **Build & Packaging**:
   - [build.py](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/build.py): Automatically groups the module files into a standard structure, sets appropriate executable (`0755`) and read-only (`0644`) file permissions, and compresses it into the standard Webmin distribution package `ntpsec.wbm.gz`.

## Verification Details

### 1. Automated Tests
I updated the mock integration test suite ([test_parser.pl](file:///Users/tonygauderman/Antigravity/webmin-ntpsec/test_parser.pl)) to mock the `WebminCore.pm` compilation and verify the namespace exports. The tests pass successfully with exit code 0:
```text
--- Testing Configuration Parser ---
Parsed 10 lines.
Driftfile: /var/lib/ntpsec/ntp.drift
Servers: 1, Pools: 1, Restricts: 3
Parser test passed successfully!

--- Testing Configuration Serializer ---
Serializer test passed successfully!

--- Testing Peers Parser ---
Parsed 3 peers.
Peers parsing test passed successfully!

--- Testing NTS Info Parser ---
NTS Info parsing test passed successfully!

--- All Tests Passed Successfully! ---
```

### 2. Syntax Validation
I ran syntax compilation checks (`perl -cw`) on all files. All scripts passed with `syntax OK`.

---

## Deployment & Installation Instructions

To install and verify the package on your TurnKey Linux server, follow these steps:

### Step 1: Copy the Package to Your Target Machine
The compiled distribution file is located at:
`/Users/tonygauderman/Antigravity/webmin-ntpsec/ntpsec.wbm.gz`

Copy this file to your TurnKey Linux machine using `scp` or a similar tool:
```bash
scp /Users/tonygauderman/Antigravity/webmin-ntpsec/ntpsec.wbm.gz root@<turnkey-ip>:/tmp/
```

### Step 2: Install via Webmin UI
1. Log in to your TurnKey Linux Webmin interface.
2. Navigate to **Webmin** -> **Webmin Configuration** -> **Webmin Modules**.
3. Under the **Install Module** tab:
   - Select **From local file**.
   - Input `/tmp/ntpsec.wbm.gz`.
4. Click **Install Module**.

*(Alternatively, you can install it under the **From uploaded file** section by uploading the `.wbm.gz` file directly from your local computer).*

### Step 3: Verify the Module & Auto-Refresh
1. Navigate to the **System** section in the Webmin sidebar menu.
2. Click on **NTPsec Client** (accompanied by the shield and clock icon).
3. Verify that the dashboard shows:
   - Service status: **Running** (or Stopped).
   - The list of active NTP peers matching your `ntpq -p` output.
   - The NTS statistics (if your servers are running with NTS).
4. Verify the **Auto-Refresh** dropdown (top-right of the dashboard):
   - Change the selector from **Off** to **5 seconds**.
   - Verify that the active peers table and service status update asynchronously every 5 seconds.
   - Click **Stop NTPsec Service** or **Start NTPsec Service** (which triggers a PJAX/AJAX page reload under Webmin's Authentic theme).
   - Confirm that the dropdown selection **persists at 5 seconds** and the automatic polling continues running without resetting to Off.
   - Navigate to another Webmin module (e.g., *Webmin Configuration*) and confirm that background polling is automatically paused to prevent resource leaks.
5. Try editing a server, adding a restrict rule, or triggering a manual sync to verify they write correctly to `/etc/ntpsec/ntp.conf` and execute system calls on the target machine.
