# Webmin Module for NTPsec Client

This Webmin module provides a complete, responsive dashboard and configuration suite for managing and monitoring the `ntpsec` time synchronization daemon on TurnKey Linux (Debian-based distributions).

---

## NTP Peer Status Icons (Tally Codes)

In the **Current NTP Peers** table, the first column displays colored status badges (known as NTP tally codes). These indicate how the NTPsec daemon is currently interacting with each time source:

| Badge | Color | Tally Code | Name | Description |
| :---: | :---: | :---: | :---: | :--- |
| **`*`** | **Green** | `sys.peer` | **System Peer** | The primary clock source currently selected by NTPsec to synchronize the system time. |
| **`+`** | **Blue** | `candidate` | **Candidate** | A high-quality server that has passed all sanity checks and is a valid backup if the system peer goes offline. |
| **`-`** | **Orange** | `outlier` | **Outlier** | The server was discarded by the clustering algorithm because its offset is too far from the group consensus. |
| **`o`** | **Grey** | `pps.peer` | **PPS Peer** | The system is synchronized directly to a local Pulse-Per-Second (PPS) hardware signal (extremely high precision). |
| **`x`** | **Grey** | `falsetick` | **Falseticker** | The server was discarded by the intersection algorithm because it deviates too far from trusted sources. |
| **`.`** | **Grey** | `excess` | **Excess** | The server was discarded simply because the maximum number of active synchronization peers was already reached. |
| *(blank)* | N/A | `reject` | **Discarded / Unused** | The server is currently unreachable, unsynchronized, or has failed sanity tests. |

> [!TIP]
> Hovering your mouse cursor over any peer status icon badge in the dashboard will display its detailed description tooltip instantly (using the `cursor: help` indicator style).

---

## Features

- **Real-Time AJAX Dashboard**: Monitor service state and synchronization peers dynamically without reloading the page.
- **Persistent Auto-Refresh**: Set auto-refresh intervals (5s, 10s, 30s, 60s, Off) which persist across page reloads using browser `localStorage` (with automatic cleanup when navigating away to prevent background leaks).
- **Time Source Management**: Easily add, edit, or delete upstream NTP `servers`, `pools`, or `peers`, with configuration options including `iburst`, `prefer`, and Network Time Security (NTS).
- **Access Control Filter Rules**: Add, edit, or delete `restrict` rules to define permissions for client synchronization and queries.
- **Security & Logging**: Configure drift files, system logs, statistics logging, tinker panic thresholds, and local NTS Server credentials.
- **Manual Time Synchronization**: Instantly step/sync system time using `ntpdig` (replaces deprecated `ntpdate`).
- **Raw Text Editor**: Modify `/etc/ntpsec/ntp.conf` directly with syntax checks.

---

## Installation & Deployment

### 1. Build the Package
On your development machine, run the build script to pack the module files into a Webmin-compatible `.wbm.gz` archive:
```bash
python3 build.py
```
This generates `ntpsec.wbm.gz` in the root directory.

### 2. Install the Module
Choose one of the two methods below to install the module on your TurnKey Linux server.

#### Method A: Direct Upload via Webmin Web Interface (Recommended)
This is the simplest method as it does not require command-line server copy commands:
1. Log in to the TurnKey Linux Webmin web interface (`https://<turnkey-ip>:12321/`).
2. Navigate to **Webmin** -> **Webmin Configuration** -> **Webmin Modules** in the left sidebar.
3. In the **Install Module** tab, select **From uploaded file**.
4. Click the file selector (**Choose File**), locate the compiled `ntpsec.wbm.gz` file on your local computer, and select it.
5. Click the **Install Module** button.

#### Method B: Local Server File Path Installation (Alternative)
Use this method if you prefer transferring the package to the server's filesystem first:
1. Transfer the archive file to your remote TurnKey Linux server using `scp`:
   ```bash
   scp ntpsec.wbm.gz root@<turnkey-ip>:/tmp/
   ```
2. Log in to the TurnKey Linux Webmin web interface.
3. Navigate to **Webmin** -> **Webmin Configuration** -> **Webmin Modules**.
4. In the **Install Module** tab, select **From local file**.
5. Input the local path on the server: `/tmp/ntpsec.wbm.gz`.
6. Click the **Install Module** button.

Once installed, the module will be accessible under **System** -> **NTPsec Client**.

---

## Usage Guide

### 1. Dashboard Status & Control
- The status box at the top shows whether the daemon is active and configured to start on boot.
- Toggle service state instantly via the **Start**, **Stop**, or **Restart** buttons.
- Click **Sync Time Now** to temporarily stop the daemon, run a network step synchronization, print the live execution output, and restart the daemon.

### 2. Upstream Time Sources
- Click **Time Sources** to manage NTP servers or pools.
- When adding a server, check **Enable Network Time Security (NTS)** to leverage secure TLS key exchange for cryptographic validation of time packets.

### 3. Access Controls
- Click **Access Control Rules** to govern which local or remote IP ranges are allowed to synchronize or query status.
- Check flags like `nomodify` (prevents run-time config changes) or `noquery` (blocks status queries from `ntpq`).

### 4. General Settings
- Click **General & Security Settings** to define file paths for logs and drift rates, or toggle specific statistics logging.
- Configure local NTS certificates and keys if you wish to run the server in NTS-server mode.
