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

# JS script for AJAX status updates
print <<'JS_EOF';
<script type='text/javascript'>
// Use a window-global variable to persist timer reference across PJAX page loads
if (window.ntpsecRefreshTimer) {
    clearInterval(window.ntpsecRefreshTimer);
    window.ntpsecRefreshTimer = null;
}

function updateStatusAjax(isManual) {
    var spinner = document.getElementById('refresh-spinner');
    if (spinner) spinner.style.display = 'inline-block';
    
    fetch('status_ajax.cgi')
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
            
            // 4. Update NTS Stats
            var ntsContainer = document.getElementById('nts-stats-container');
            if (ntsContainer) {
                if (data.nts) {
                    var ntsHtml = "<hr><h3>Network Time Security (NTS) Status</h3>" +
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
    initTooltips();
})();
</script>
JS_EOF

&ui_print_footer("/", $text{'index'});
