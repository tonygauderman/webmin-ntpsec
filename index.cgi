#!/usr/bin/perl
# index.cgi
# Main page showing NTPsec daemon status, peers, and configurations.

use WebminCore;
require './ntpsec-lib.pl';

&ui_print_header(undef, $text{'index_title'}, "", undef, 1, 1);

# 0. Refresh controls
print "
<div style='margin-bottom: 15px; display: flex; justify-content: flex-end; align-items: center; gap: 10px;'>
  <button id='manual-refresh-btn' class='btn btn-default btn-sm' onclick='updateStatusAjax(true)' style='margin: 0; padding: 4px 10px;'>
    <i class='fa fa-refresh'></i> Refresh
  </button>
  <span style='font-size: 0.9em; color: #666; margin-left: 10px;'>Auto Refresh:</span>
  <select id='auto-refresh-select' class='form-control input-sm' style='width: 120px; display: inline-block; margin: 0; height: 30px; padding: 2px 6px;' onchange='changeAutoRefresh(this.value)'>
    <option value='off'>Off</option>
    <option value='5'>5 seconds</option>
    <option value='10'>10 seconds</option>
    <option value='30'>30 seconds</option>
    <option value='60'>60 seconds</option>
  </select>
  <span id='refresh-spinner' style='display: none; color: #0284c7; margin-left: 5px;'><i class='fa fa-spinner fa-spin'></i></span>
</div>
";

# 1. Daemon Status and Service Controls
my ($running, $enabled) = &get_ntp_status();

print &ui_table_start($text{'index_status'}, "width=100%", 2);

# Status cell
my $status_text = "<span id='status-display'>" . ($running ? 
    "<span style='color:green; font-weight:bold; font-size:1.1em;'>$text{'index_running'}</span>" :
    "<span style='color:red; font-weight:bold; font-size:1.1em;'>$text{'index_stopped'}</span>") . "</span>";
print &ui_table_row("Status", $status_text);

# Controls cell
my $control_form = &ui_form_start("action.cgi", "post");
$control_form .= "<span id='control-buttons-container'>";
if ($running) {
    $control_form .= &ui_submit($text{'index_stop'}, "stop", undef, undef, "class='btn btn-danger'");
    $control_form .= " " . &ui_submit($text{'index_restart'}, "restart", undef, undef, "class='btn btn-warning'");
} else {
    $control_form .= &ui_submit($text{'index_start'}, "start", undef, undef, "class='btn btn-success'");
}
$control_form .= "</span>";
$control_form .= "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;";
$control_form .= &ui_checkbox("boot", 1, $text{'index_boot'}, $enabled, "onclick='form.submit()'");
$control_form .= &ui_form_end();
print &ui_table_row("Service Control", $control_form);

# Manual Time Sync cell
my $sync_form = &ui_form_start("sync.cgi", "post");
$sync_form .= &ui_submit($text{'index_sync'}, "sync", undef, undef, "class='btn btn-primary'");
$sync_form .= "<div style='margin-top: 5px; color: #666; font-size: 0.9em;'>$text{'index_sync_desc'}</div>";
$sync_form .= &ui_form_end();
print &ui_table_row("Manual Sync", $sync_form);

print &ui_table_end();
print "<br>\n";

# 2. Navigation Buttons/Grid
print &ui_subheading($text{'index_buttons'});

my @links = (
    "edit_servers.cgi",
    "edit_restrict.cgi",
    "edit_misc.cgi",
    "edit_manual.cgi"
);
my @titles = (
    $text{'index_edit_servers'},
    $text{'index_edit_restrict'},
    $text{'index_edit_misc'},
    $text{'index_edit_manual'}
);
my @descs = (
    $text{'index_edit_servers_desc'},
    $text{'index_edit_restrict_desc'},
    $text{'index_edit_misc_desc'},
    $text{'index_edit_manual_desc'}
);

print "<table width='100%'>\n";
for (my $i = 0; $i < @links; $i += 2) {
    print "<tr>\n";
    for (my $j = 0; $j < 2; $j++) {
        my $k = $i + $j;
        print "<td width='50%' valign='top' style='padding: 5px;'>\n";
        if ($k < @links) {
            my $btn_html = "<div style='padding:15px; border:1px solid #ddd; border-radius:4px; margin-bottom:15px; background:#fafafa;'>";
            $btn_html .= "<a href='$links[$k]' style='font-size:1.2em; font-weight:bold; display:inline-block; margin-bottom:5px;'>$titles[$k]</a><br>";
            $btn_html .= "<span style='color:#666; font-size:0.95em;'>$descs[$k]</span>";
            $btn_html .= "</div>";
            print $btn_html;
        }
        print "</td>\n";
    }
    print "</tr>\n";
}
print "</table>\n";
print "<br>\n";

# 3. Peers status
print &ui_subheading($text{'index_peers'});
my $peers = &get_ntpq_peers();

my @headers = (
    "",
    $text{'index_remote'},
    $text{'index_refid'},
    $text{'index_st'},
    $text{'index_t'},
    $text{'index_when'},
    $text{'index_poll'},
    $text{'index_reach'},
    $text{'index_delay'},
    $text{'index_offset'},
    $text{'index_jitter'}
);

my @rows;
foreach my $p (@$peers) {
    my $flag_html = &get_peer_flag_html($p->{'flag'});
    
    push(@rows, [
        $flag_html,
        $p->{'remote'},
        $p->{'refid'},
        $p->{'st'},
        $p->{'type'},
        $p->{'when'},
        $p->{'poll'},
        $p->{'reach'},
        $p->{'delay'},
        $p->{'offset'},
        $p->{'jitter'}
    ]);
}

print "<div id='peers-table-container'>\n";
if (@rows) {
    print &ui_columns_table(\@headers, undef, \@rows);
} else {
    print "<div class='alert alert-warning'>$text{'index_no_peers'}</div>\n";
}
print "</div>\n";

# 4. Generic NTP Traffic Statistics
my $sysstats = &get_sys_stats();
my $monstats = &get_ntp_monstats();
my $mru = &get_ntp_mru();
print "<div id='sysstats-container'>\n";
if (defined($sysstats)) {
    print &ui_subheading("NTP Traffic Statistics");
    print "<table width='100%'><tr><td width='33%' valign='top'>\n";
    print &ui_table_start("System & Client Summary", "width=100%", 2);
    print &ui_table_row("Uptime", $sysstats->{'uptime'});
    print &ui_table_row("Total Packets Received", $sysstats->{'packets received'});
    print &ui_table_row("Packets Processed for Time", $sysstats->{'processed for time'});
    my $upstreams = &get_ntp_mru_upstreams();
    print &ui_table_row("Active Clients", scalar(@$mru));
    print &ui_table_row("Upstream Servers", $upstreams);
    print &ui_table_end();
    
    print "</td><td width='34%' valign='top'>\n";
    print &ui_table_start("Legacy vs Modern Traffic", "width=100%", 2);
    print &ui_table_row("Modern NTPv4 Packets", $sysstats->{'current version'} || 0);
    print &ui_table_row("Legacy NTPv3/2/1 Packets", $sysstats->{'old version'} || 0);
    print &ui_table_end();

    print "</td><td width='33%' valign='top'>\n";
    print &ui_table_start("Packet Filter & Rejections", "width=100%", 2);
    print &ui_table_row("Packets Restricted", $sysstats->{'restricted'});
    print &ui_table_row("Packets Rate Limited", $sysstats->{'rate limited'});
    print &ui_table_row("KoD Responses Sent", $sysstats->{'kod responses'} || 0);
    print &ui_table_row("Authentication Failed", $sysstats->{'authentication failed'});
    print &ui_table_row("Malformed Packets", $sysstats->{'bad length or format'} || 0);
    print &ui_table_end();
    print "</td></tr></table>\n";
    print "<br>\n";
}
print "</div>\n";

# 5. Recent Client Connections (MRU List)
print &ui_subheading("Recent Client Connections");
print "<div id='mru-container'></div>\n";
print "<br>\n";



# 3. NTS diagnostics if active
my $nts = &get_nts_info();
print "<div id='nts-stats-container'>\n";
if (defined($nts)) {
    print &ui_subheading("Network Time Security (NTS) Status");
    
    my @client_rows;
    my @server_rows;
    foreach my $k (sort keys %$nts) {
        if ($k =~ /client|cookie|probe/i) {
            push(@client_rows, [ "<b>$k</b>", $nts->{$k} ]);
        } else {
            push(@server_rows, [ "<b>$k</b>", $nts->{$k} ]);
        }
    }
    
    print "<table width='100%'><tr><td width='50%' valign='top'>\n";
    
    # Client stats
    print &ui_table_start("NTS Client Statistics", "width=100%", 2);
    foreach my $r (@client_rows) {
        print &ui_table_row($r->[0], $r->[1]);
    }
    print &ui_table_end();
    
    print "</td><td width='50%' valign='top'>\n";
    
    # Server stats
    print &ui_table_start("NTS Server / KE Statistics", "width=100%", 2);
    foreach my $r (@server_rows) {
        print &ui_table_row($r->[0], $r->[1]);
    }
    print &ui_table_end();
    
    print "</td></tr></table>\n";
    print "<br>\n";
}
print "</div>\n";

# Serialize initial MRU data
my @mru_jsons;
foreach my $entry (@$mru) {
    my $ejson = "{";
    my @e_kv;
    foreach my $k (keys %$entry) {
        my $v = $entry->{$k};
        $v =~ s/\\/\\\\/g;
        $v =~ s/"/\\"/g;
        $v =~ s/\n/\\n/g;
        $v =~ s/\r/\\r/g;
        push(@e_kv, "\"$k\":\"$v\"");
    }
    $ejson .= join(",", @e_kv);
    $ejson .= "}";
    push(@mru_jsons, $ejson);
}
my $mru_initial_json = "[" . join(",", @mru_jsons) . "]";

# JS script for AJAX status updates
print <<JS_EOF;
<script type='text/javascript'>
window.ntpsecMruData = $mru_initial_json;
window.ntpsecMruPage = 1;
window.ntpsecMruPageSize = '10';
window.ntpsecMruSearch = "";
window.ntpsecMruSortCol = 'lstint';
window.ntpsecMruSortDir = 1;
JS_EOF

print <<'JS_EOF';
// Use a window-global variable to persist timer reference across PJAX page loads
if (window.ntpsecRefreshTimer) {
    clearInterval(window.ntpsecRefreshTimer);
    window.ntpsecRefreshTimer = null;
}

function updateStatusAjax(isManual) {
    var spinner = document.getElementById('refresh-spinner');
    if (spinner) spinner.style.display = 'inline-block';
    
    fetch('status_ajax.cgi?t=' + new Date().getTime())
        .then(response => response.json())
        .then(data => {
            // 1. Update Status Text
            var statusDisp = document.getElementById('status-display');
            if (statusDisp) statusDisp.innerHTML = data.status_html;
            
            // 2. Update Service Control Buttons
            var btnContainer = document.getElementById('control-buttons-container');
            if (btnContainer) {
                var btnHtml = "";
                if (data.running) {
                    btnHtml = "<input type='submit' name='stop' value='Stop NTPsec Service' class='btn btn-danger'> " +
                              "<input type='submit' name='restart' value='Restart NTPsec Service' class='btn btn-warning'>";
                } else {
                    btnHtml = "<input type='submit' name='start' value='Start NTPsec Service' class='btn btn-success'>";
                }
                btnContainer.innerHTML = btnHtml;
            }
            
            // 3. Update Peers Table
            var peersContainer = document.getElementById('peers-table-container');
            if (peersContainer) {
                if (data.peers && data.peers.length > 0) {
                    var tableHtml = "<table class='table table-striped table-hover table-bordered ui_table'>\n" +
                        "<thead><tr class='ui_table_head'>" +
                        "<th></th>" +
                        "<th>Remote Server/Pool</th>" +
                        "<th>Reference ID</th>" +
                        "<th>Stratum</th>" +
                        "<th>Type</th>" +
                        "<th>When (s)</th>" +
                        "<th>Poll (s)</th>" +
                        "<th>Reach</th>" +
                        "<th>Delay (ms)</th>" +
                        "<th>Offset (ms)</th>" +
                        "<th>Jitter (ms)</th>" +
                        "</tr></thead><tbody>";
                        
                    data.peers.forEach(function(p) {
                        tableHtml += "<tr>" +
                            "<td style='text-align:center;'>" + p.flag_html + "</td>" +
                            "<td><b>" + p.remote + "</b></td>" +
                            "<td>" + p.refid + "</td>" +
                            "<td>" + p.st + "</td>" +
                            "<td>" + p.type + "</td>" +
                            "<td>" + p.when + "</td>" +
                            "<td>" + p.poll + "</td>" +
                            "<td>" + p.reach + "</td>" +
                            "<td>" + p.delay + "</td>" +
                            "<td>" + p.offset + "</td>" +
                            "<td>" + p.jitter + "</td>" +
                            "</tr>";
                    });
                    tableHtml += "</tbody></table>";
                    peersContainer.innerHTML = tableHtml;
                } else {
                    peersContainer.innerHTML = "<div class='alert alert-warning'>No active NTP peers found.</div>";
                }
            }
            
            // 3.5. Update Generic NTP Stats
            var sysContainer = document.getElementById('sysstats-container');
            if (sysContainer) {
                if (data.sysstats) {
                    var mon = data.monstats || {};
                    var sysHtml = "<h3 class='ui_subheading'>NTP Traffic Statistics</h3>" +
                        "<table width='100%'><tr><td width='33%' valign='top'>" +
                        "<table class='table table-striped table-hover table-bordered ui_table'>" +
                        "<thead><tr class='ui_table_head'><th colspan='2'>System & Client Summary</th></tr></thead><tbody>" +
                        "<tr><td>Uptime</td><td>" + (data.sysstats['uptime'] || '0') + "</td></tr>" +
                        "<tr><td>Total Packets Received</td><td>" + (data.sysstats['packets received'] || '0') + "</td></tr>" +
                        "<tr><td>Packets Processed for Time</td><td>" + (data.sysstats['processed for time'] || '0') + "</td></tr>" +
                        "<tr><td>Active Clients</td><td>" + (data.mru ? data.mru.length : '0') + "</td></tr>" +
                        "<tr><td>Upstream Servers</td><td>" + (data.upstream_servers || '0') + "</td></tr>" +
                        "</tbody></table></td><td width='34%' valign='top'>" +
                        "<table class='table table-striped table-hover table-bordered ui_table'>" +
                        "<thead><tr class='ui_table_head'><th colspan='2'>Legacy vs Modern Traffic</th></tr></thead><tbody>" +
                        "<tr><td>Modern NTPv4 Packets</td><td>" + (data.sysstats['current version'] || '0') + "</td></tr>" +
                        "<tr><td>Legacy NTPv3/2/1 Packets</td><td>" + (data.sysstats['old version'] || '0') + "</td></tr>" +
                        "</tbody></table></td><td width='33%' valign='top'>" +
                        "<table class='table table-striped table-hover table-bordered ui_table'>" +
                        "<thead><tr class='ui_table_head'><th colspan='2'>Packet Filter & Rejections</th></tr></thead><tbody>" +
                        "<tr><td>Packets Restricted</td><td>" + (data.sysstats['restricted'] || '0') + "</td></tr>" +
                        "<tr><td>Packets Rate Limited</td><td>" + (data.sysstats['rate limited'] || '0') + "</td></tr>" +
                        "<tr><td>KoD Responses Sent</td><td>" + (data.sysstats['kod responses'] || '0') + "</td></tr>" +
                        "<tr><td>Authentication Failed</td><td>" + (data.sysstats['authentication failed'] || '0') + "</td></tr>" +
                        "<tr><td>Malformed Packets</td><td>" + (data.sysstats['bad length or format'] || '0') + "</td></tr>" +
                        "</tbody></table></td></tr></table><br>";
                    sysContainer.innerHTML = sysHtml;
                } else {
                    sysContainer.innerHTML = "";
                }
            }

            // 3.7. Update MRU Client Stats
            if (data.mru) {
                window.ntpsecMruData = data.mru;
                renderMruTable();
            }

            // 4. Update NTS Stats
            var ntsContainer = document.getElementById('nts-stats-container');
            if (ntsContainer) {
                if (data.nts) {
                    var ntsHtml = "<hr><h3 class='ui_subheading'>Network Time Security (NTS) Status</h3>" +
                        "<table width='100%'><tr><td width='50%' valign='top'>" +
                        "<table class='table table-striped table-hover table-bordered ui_table'>" +
                        "<thead><tr class='ui_table_head'><th colspan='2'>NTS Client Statistics</th></tr></thead><tbody>";
                    
                    var keys = Object.keys(data.nts).sort();
                    var clientKeys = keys.filter(k => k.toLowerCase().match(/client|cookie|probe/));
                    var serverKeys = keys.filter(k => !k.toLowerCase().match(/client|cookie|probe/));
                    
                    clientKeys.forEach(function(k) {
                        ntsHtml += "<tr><td><b>" + k + "</b></td><td>" + data.nts[k] + "</td></tr>";
                    });
                    ntsHtml += "</tbody></table></td><td width='50%' valign='top'>" +
                        "<table class='table table-striped table-hover table-bordered ui_table'>" +
                        "<thead><tr class='ui_table_head'><th colspan='2'>NTS Server / KE Statistics</th></tr></thead><tbody>";
                        
                    serverKeys.forEach(function(k) {
                        ntsHtml += "<tr><td><b>" + k + "</b></td><td>" + data.nts[k] + "</td></tr>";
                    });
                    ntsHtml += "</tbody></table></td></tr></table><br>";
                    ntsContainer.innerHTML = ntsHtml;
                } else {
                    ntsContainer.innerHTML = "";
                }
            }
            initTooltips();
        })
        .catch(err => console.error('Error fetching status:', err))
        .finally(() => {
            if (spinner) spinner.style.display = 'none';
        });
}

function changeAutoRefresh(val) {
    localStorage.setItem('ntpsec_refresh_interval', val);
    if (window.ntpsecRefreshTimer) {
        clearInterval(window.ntpsecRefreshTimer);
        window.ntpsecRefreshTimer = null;
    }
    if (val !== 'off') {
        var sec = parseInt(val, 10);
        window.ntpsecRefreshTimer = setInterval(function() {
            var select = document.getElementById('auto-refresh-select');
            if (!select) {
                // Clear the timer if we navigated away from the module page via PJAX
                clearInterval(window.ntpsecRefreshTimer);
                window.ntpsecRefreshTimer = null;
                return;
            }
            updateStatusAjax(false);
        }, sec * 1000);
    }
}

function initTooltips() {
    if (typeof jQuery !== 'undefined' && jQuery.fn && jQuery.fn.tooltip) {
        try {
            jQuery('[data-toggle="tooltip"]').tooltip({ container: 'body', trigger: 'hover' });
        } catch(e) {
            console.log('Tooltip init error:', e);
        }
    }
}

function renderMruTable() {
    var container = document.getElementById('mru-container');
    if (!container) return;
    
    // 1. Filter data based on search
    var query = (window.ntpsecMruSearch || '').trim().toLowerCase();
    var filtered = window.ntpsecMruData || [];
    if (query !== '') {
        filtered = filtered.filter(function(e) {
            return (e.addr || '').toLowerCase().indexOf(query) !== -1;
        });
    }
    
    // 2. Sort data
    var col = window.ntpsecMruSortCol;
    var dir = window.ntpsecMruSortDir;
    filtered.sort(function(a, b) {
        var valA = a[col];
        var valB = b[col];
        if (col === 'lstint' || col === 'avgint' || col === 'count' || col === 'rport') {
            valA = parseFloat(valA) || 0;
            valB = parseFloat(valB) || 0;
        } else {
            valA = (valA || '').toString().toLowerCase();
            valB = (valB || '').toString().toLowerCase();
        }
        if (valA < valB) return -1 * dir;
        if (valA > valB) return 1 * dir;
        return 0;
    });
    
    // 3. Paginate data
    var total = filtered.length;
    var pageSize = window.ntpsecMruPageSize;
    var maxPage = 1;
    var paginated = filtered;
    
    if (pageSize !== 'all') {
        var size = parseInt(pageSize, 10);
        maxPage = Math.ceil(total / size) || 1;
        if (window.ntpsecMruPage > maxPage) {
            window.ntpsecMruPage = maxPage;
        }
        var start = (window.ntpsecMruPage - 1) * size;
        paginated = filtered.slice(start, start + size);
    }
    
    // Helper to generate header sort indicator
    function getSortIndicator(headerCol) {
        if (window.ntpsecMruSortCol === headerCol) {
            return window.ntpsecMruSortDir === 1 ? ' &#9650;' : ' &#9660;';
        }
        return '';
    }
    
    // Generate controls HTML
    var html = "<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 10px;'>" +
        "<div>" +
        "Show <select id='mru-size-select' class='form-control' style='display:inline-block; width:70px; min-width:70px; height:auto; padding:4px 8px;' onchange='changeMruSize(this.value)'>" +
        "<option value='10'" + (pageSize === '10' ? " selected" : "") + ">10</option>" +
        "<option value='20'" + (pageSize === '20' ? " selected" : "") + ">20</option>" +
        "<option value='50'" + (pageSize === '50' ? " selected" : "") + ">50</option>" +
        "<option value='all'" + (pageSize === 'all' ? " selected" : "") + ">All</option>" +
        "</select> entries" +
        "</div>" +
        "<div>" +
        "Search: <input type='text' id='mru-search-input' class='form-control' placeholder='Search IP address...' style='display:inline-block; width:200px; height:auto; padding:4px 8px;' value='" + (window.ntpsecMruSearch || '') + "' oninput='filterMruSearch(this.value)'>" +
        "</div>" +
        "</div>";
        
    if (total > 0) {
        html += "<table class='table table-striped table-hover table-bordered ui_table'>" +
            "<thead><tr class='ui_table_head'>" +
            "<th style='cursor:pointer;' onclick='sortMruTable(\"addr\")'>IP Address" + getSortIndicator('addr') + "</th>" +
            "<th style='cursor:pointer;' onclick='sortMruTable(\"rport\")'>Port" + getSortIndicator('rport') + "</th>" +
            "<th style='cursor:pointer;' onclick='sortMruTable(\"count\")'>Queries" + getSortIndicator('count') + "</th>" +
            "<th style='cursor:pointer;' onclick='sortMruTable(\"lstint\")'>Last Query" + getSortIndicator('lstint') + "</th>" +
            "<th style='cursor:pointer;' onclick='sortMruTable(\"avgint\")'>Average Interval" + getSortIndicator('avgint') + "</th>" +
            "<th style='cursor:pointer;' onclick='sortMruTable(\"rstr\")'>Flags" + getSortIndicator('rstr') + "</th>" +
            "</tr></thead><tbody>";
            
        paginated.forEach(function(e) {
            var last = e.lstint == 0 ? "now" : e.lstint + "s ago";
            var avg = e.avgint ? e.avgint + "s" : "N/A";
            html += "<tr>" +
                "<td>" + e.addr + "</td>" +
                "<td>" + (e.rport || "123") + "</td>" +
                "<td>" + (e.count || "0") + "</td>" +
                "<td>" + last + "</td>" +
                "<td>" + avg + "</td>" +
                "<td>" + (e.rstr || "0x0") + "</td>" +
                "</tr>";
        });
        html += "</tbody></table>";
        
        // Pagination info and buttons
        var startEntry = pageSize === 'all' ? 1 : (window.ntpsecMruPage - 1) * parseInt(pageSize, 10) + 1;
        if (total === 0) startEntry = 0;
        var endEntry = pageSize === 'all' ? total : Math.min(window.ntpsecMruPage * parseInt(pageSize, 10), total);
        
        html += "<div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-top: 10px;'>" +
            "<div>Showing " + startEntry + " to " + endEntry + " of " + total + " entries" + (query !== '' ? " (filtered)" : "") + "</div>" +
            "<div>" +
            "<button class='btn btn-default btn-sm' onclick='navigateMruPage(1)' " + (window.ntpsecMruPage === 1 ? "disabled" : "") + ">First</button> " +
            "<button class='btn btn-default btn-sm' onclick='navigateMruPage(" + (window.ntpsecMruPage - 1) + ")' " + (window.ntpsecMruPage === 1 ? "disabled" : "") + ">Previous</button> " +
            "<span style='margin: 0 10px;'>Page " + window.ntpsecMruPage + " of " + maxPage + "</span>" +
            "<button class='btn btn-default btn-sm' onclick='navigateMruPage(" + (window.ntpsecMruPage + 1) + ")' " + (window.ntpsecMruPage === maxPage ? "disabled" : "") + ">Next</button> " +
            "<button class='btn btn-default btn-sm' onclick='navigateMruPage(" + maxPage + ")' " + (window.ntpsecMruPage === maxPage ? "disabled" : "") + ">Last</button>" +
            "</div>" +
            "</div>";
    } else {
        html += "<div class='alert alert-info'>No recent client connections found.</div>";
    }
    
    // Save search input focus
    var searchFocused = false;
    var activeEl = document.activeElement;
    if (activeEl && activeEl.id === 'mru-search-input') {
        searchFocused = true;
    }
    
    container.innerHTML = html;
    
    // Refocus search input if it was active
    if (searchFocused) {
        var searchInput = document.getElementById('mru-search-input');
        if (searchInput) {
            searchInput.focus();
            var val = searchInput.value;
            searchInput.value = '';
            searchInput.value = val;
        }
    }
}

window.changeMruSize = function(val) {
    window.ntpsecMruPageSize = val;
    window.ntpsecMruPage = 1;
    renderMruTable();
};

window.filterMruSearch = function(val) {
    window.ntpsecMruSearch = val;
    window.ntpsecMruPage = 1;
    renderMruTable();
};

window.sortMruTable = function(col) {
    if (window.ntpsecMruSortCol === col) {
        window.ntpsecMruSortDir = -window.ntpsecMruSortDir;
    } else {
        window.ntpsecMruSortCol = col;
        window.ntpsecMruSortDir = 1;
    }
    renderMruTable();
};

window.navigateMruPage = function(p) {
    window.ntpsecMruPage = p;
    renderMruTable();
};

// Initial setup on page load (executed immediately since script is at the end of the DOM)
(function() {
    var savedInterval = localStorage.getItem('ntpsec_refresh_interval') || 'off';
    var select = document.getElementById('auto-refresh-select');
    if (select) {
        select.value = savedInterval;
    }
    if (savedInterval !== 'off') {
        changeAutoRefresh(savedInterval);
    }
    renderMruTable();
    initTooltips();
})();
</script>
JS_EOF

&ui_print_footer("/", $text{'index'});
