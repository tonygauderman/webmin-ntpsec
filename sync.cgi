#!/usr/bin/perl
# sync.cgi
# Stops NTPsec daemon, runs ntpdig -S to sync time, and restarts the daemon.

use WebminCore;
require './ntpsec-lib.pl';

# Disable buffering so output streams to browser in real-time
$| = 1;

&ui_print_header(undef, $text{'sync_title'}, "");

print "<h4>$text{'sync_doing'}</h4>\n";
print "<pre style='background:#000; color:#fff; padding:15px; border-radius:4px; font-family:monospace;'>";

# 1. Stop NTPsec daemon
print "Stopping NTPsec service...\n";
my ($stop_ok, $stop_err) = &service_action('stop');
if ($stop_ok) {
    print "Service stopped successfully.\n\n";
} else {
    print "Warning: Failed to stop service (it might already be stopped): $stop_err\n\n";
}

# 2. Gather servers/pools from configuration
my $conf = &get_ntp_config();
my @hosts;
foreach my $item (@$conf) {
    if ($item->{'type'} eq 'server' || $item->{'type'} eq 'pool') {
        push(@hosts, $item->{'address'});
    }
}

# Fallback to pool.ntp.org if none configured
if (!@hosts) {
    print "No time sources found in configuration. Using pool.ntp.org as fallback.\n";
    push(@hosts, 'pool.ntp.org');
}

# 3. Execute ntpdig -S
my $ntpdig = $config{'ntpdig_path'} || '/usr/bin/ntpdig';
my $sync_ok = 0;

if (-x $ntpdig) {
    my $cmd = quotemeta($ntpdig) . " -S " . join(" ", map { quotemeta($_) } @hosts);
    print "Executing: ntpdig -S " . join(" ", @hosts) . "\n";
    
    # Run and stream output
    open(my $pipe, "$cmd 2>&1 |");
    if ($pipe) {
        while (my $line = <$pipe>) {
            print &html_escape($line);
        }
        close($pipe);
        $sync_ok = ($? == 0);
    } else {
        print "Error: Failed to run sync command: $!\n";
    }
} else {
    print "Error: ntpdig binary not found or not executable at $ntpdig.\n";
    print "Please check module configuration.\n";
}

# 4. Start NTPsec daemon back up
print "\nStarting NTPsec service...\n";
my ($start_ok, $start_err) = &service_action('start');
if ($start_ok) {
    print "Service started successfully.\n";
} else {
    print "Error: Failed to restart NTPsec service: $start_err\n";
}

print "</pre>";

# 5. Report results
if ($sync_ok) {
    print "<div class='alert alert-success' style='margin:15px 0;'><b>$text{'sync_success'}</b></div>\n";
} else {
    print "<div class='alert alert-danger' style='margin:15px 0;'><b>$text{'sync_failed'}</b></div>\n";
}

# Webmin back button
print "<a href='index.cgi' class='btn btn-default' style='margin-top:10px;'>&larr; $text{'sync_back'}</a><br>\n";

&ui_print_footer("", $text{'index_title'});
