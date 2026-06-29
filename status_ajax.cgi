#!/usr/bin/perl
# status_ajax.cgi
# Returns system status and peers in JSON format.

use WebminCore;
require './ntpsec-lib.pl';

&init_config();

# Print JSON headers with cache prevention
print "Cache-Control: no-cache, no-store, must-revalidate\n";
print "Pragma: no-cache\n";
print "Expires: 0\n";
print "Content-type: application/json\n\n";

my ($running, $enabled) = &get_ntp_status();
my $peers = &get_ntpq_peers();
my $nts = &get_nts_info();
my $sysstats = &get_sys_stats();
my $mru = &get_ntp_mru();
my $monstats = &get_ntp_monstats();
my $upstream_servers = &get_ntp_mru_upstreams();

# Escape strings helper for valid JSON
sub json_escape {
    my ($s) = @_;
    return "" if (!defined($s));
    $s =~ s/\\/\\\\/g;
    $s =~ s/"/\\"/g;
    $s =~ s/\n/\\n/g;
    $s =~ s/\r/\\r/g;
    $s =~ s/\t/\\t/g;
    return $s;
}

# Construct JSON manually to be 100% dependency-free
my $json = "{";
$json .= "\"running\":" . ($running ? "true" : "false") . ",";
$json .= "\"enabled\":" . ($enabled ? "true" : "false") . ",";

# Status HTML representation
my $status_html = $running ? 
    "<span style='color:green; font-weight:bold; font-size:1.1em;'>$text{'index_running'}</span>" :
    "<span style='color:red; font-weight:bold; font-size:1.1em;'>$text{'index_stopped'}</span>";
$json .= "\"status_html\":\"" . &json_escape($status_html) . "\",";

# Peers array
$json .= "\"peers\":[";
my @peer_jsons;
foreach my $p (@$peers) {
    my $flag_html = &get_peer_flag_html($p->{'flag'});
    
    my $pjson = "{";
    $pjson .= "\"flag_html\":\"" . &json_escape($flag_html) . "\",";
    $pjson .= "\"remote\":\"" . &json_escape($p->{'remote'}) . "\",";
    $pjson .= "\"refid\":\"" . &json_escape($p->{'refid'}) . "\",";
    $pjson .= "\"st\":\"" . &json_escape($p->{'st'}) . "\",";
    $pjson .= "\"type\":\"" . &json_escape($p->{'type'}) . "\",";
    $pjson .= "\"when\":\"" . &json_escape($p->{'when'}) . "\",";
    $pjson .= "\"poll\":\"" . &json_escape($p->{'poll'}) . "\",";
    $pjson .= "\"reach\":\"" . &json_escape($p->{'reach'}) . "\",";
    $pjson .= "\"delay\":\"" . &json_escape($p->{'delay'}) . "\",";
    $pjson .= "\"offset\":\"" . &json_escape($p->{'offset'}) . "\",";
    $pjson .= "\"jitter\":\"" . &json_escape($p->{'jitter'}) . "\"";
    $pjson .= "}";
    push(@peer_jsons, $pjson);
}
$json .= join(",", @peer_jsons);
$json .= "],";

# Generic NTP stats
if (defined($sysstats)) {
    $json .= "\"sysstats\":{";
    my @sys_kv;
    foreach my $k (keys %$sysstats) {
        push(@sys_kv, "\"" . &json_escape($k) . "\":\"" . &json_escape($sysstats->{$k}) . "\"");
    }
    $json .= join(",", @sys_kv);
    $json .= "},";
} else {
    $json .= "\"sysstats\":null,";
}

# MRU list
$json .= "\"mru\":[";
my @mru_jsons;
foreach my $entry (@$mru) {
    my $ejson = "{";
    my @e_kv;
    foreach my $k (keys %$entry) {
        push(@e_kv, "\"" . &json_escape($k) . "\":\"" . &json_escape($entry->{$k}) . "\"");
    }
    $ejson .= join(",", @e_kv);
    $ejson .= "}";
    push(@mru_jsons, $ejson);
}
$json .= join(",", @mru_jsons);
$json .= "],";
$json .= "\"upstream_servers\":\"" . &json_escape($upstream_servers) . "\",";

# Monstats
if (defined($monstats)) {
    $json .= "\"monstats\":{";
    my @mon_kv;
    foreach my $k (keys %$monstats) {
        push(@mon_kv, "\"" . &json_escape($k) . "\":\"" . &json_escape($monstats->{$k}) . "\"");
    }
    $json .= join(",", @mon_kv);
    $json .= "},";
} else {
    $json .= "\"monstats\":null,";
}

# NTS stats
if (defined($nts)) {
    $json .= "\"nts\":{";
    my @nts_kv;
    foreach my $k (keys %$nts) {
        push(@nts_kv, "\"" . &json_escape($k) . "\":\"" . &json_escape($nts->{$k}) . "\"");
    }
    $json .= join(",", @nts_kv);
    $json .= "}";
} else {
    $json .= "\"nts\":null";
}

$json .= "}";
print $json;
