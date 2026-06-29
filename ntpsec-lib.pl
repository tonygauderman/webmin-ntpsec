# ntpsec-lib.pl
# Shared functions for NTPsec module

use WebminCore;
&init_config();

# get_ntp_config()
# Parses /etc/ntpsec/ntp.conf (or configured file) into an array of hash references.
sub get_ntp_config {
    my $file = $_[0] || $config{'ntp_conf'} || '/etc/ntpsec/ntp.conf';
    my @rv;
    if (!-r $file) {
        return \@rv;
    }
    open(my $fh, "<", $file) || return \@rv;
    my $line_no = 0;
    while(my $line = <$fh>) {
        $line =~ s/\r?\n//;
        my $orig = $line;
        
        # Split comment
        my $comment = "";
        if ($line =~ s/#(.*)$//) {
            $comment = $1;
            $comment =~ s/^\s+//;
            $comment =~ s/\s+$//;
        }
        
        # Trim leading/trailing whitespace
        my $trimmed = $line;
        $trimmed =~ s/^\s+//;
        $trimmed =~ s/\s+$//;
        
        my $item = {
            'line' => $line_no,
            'orig' => $orig,
            'comment' => $comment,
            'type' => 'other',
            'value' => $trimmed
        };
        
        if ($trimmed eq '') {
            $item->{'type'} = 'empty';
        } elsif ($trimmed =~ /^(server|pool|peer)\s+(\S+)(.*)$/i) {
            my $type = lc($1);
            my $address = $2;
            my $opts_str = $3;
            $opts_str =~ s/^\s+//;
            $opts_str =~ s/\s+$//;
            
            my %opts;
            my @tokens = split(/\s+/, $opts_str);
            for (my $i=0; $i<@tokens; $i++) {
                my $tok = $tokens[$i];
                if ($tok eq 'minpoll' || $tok eq 'maxpoll' || $tok eq 'port') {
                    $opts{$tok} = $tokens[$i+1];
                    $i++;
                } elsif ($tok ne '') {
                    $opts{$tok} = 1;
                }
            }
            $item->{'type'} = $type;
            $item->{'address'} = $address;
            $item->{'options'} = \%opts;
        } elsif ($trimmed =~ /^restrict\s+(\S+)(.*)$/i) {
            my $address = $1;
            my $rest = $2;
            $rest =~ s/^\s+//;
            $rest =~ s/\s+$//;
            
            my $mask;
            my @flags;
            my @tokens = split(/\s+/, $rest);
            for (my $i=0; $i<@tokens; $i++) {
                if (lc($tokens[$i]) eq 'mask') {
                    $mask = $tokens[$i+1];
                    $i++;
                } elsif ($tokens[$i] ne '') {
                    push(@flags, $tokens[$i]);
                }
            }
            $item->{'type'} = 'restrict';
            $item->{'address'} = $address;
            $item->{'mask'} = $mask;
            $item->{'flags'} = \@flags;
        } elsif ($trimmed =~ /^driftfile\s+(\S+)/i) {
            $item->{'type'} = 'driftfile';
            $item->{'value'} = $1;
        } elsif ($trimmed =~ /^logfile\s+(\S+)/i) {
            $item->{'type'} = 'logfile';
            $item->{'value'} = $1;
        } elsif ($trimmed =~ /^statsdir\s+(\S+)/i) {
            $item->{'type'} = 'statsdir';
            $item->{'value'} = $1;
        } elsif ($trimmed =~ /^statistics\s+(.*)/i) {
            $item->{'type'} = 'statistics';
            my $stats = $1;
            $stats =~ s/^\s+//;
            $stats =~ s/\s+$//;
            $item->{'value'} = $stats;
        } elsif ($trimmed =~ /^tinker\s+panic\s+(\d+)/i) {
            $item->{'type'} = 'tinker_panic';
            $item->{'value'} = $1;
        } elsif ($trimmed =~ /^nts\s+cert\s+(\S+)/i) {
            $item->{'type'} = 'nts_cert';
            $item->{'value'} = $1;
        } elsif ($trimmed =~ /^nts\s+key\s+(\S+)/i) {
            $item->{'type'} = 'nts_key';
            $item->{'value'} = $1;
        } elsif ($trimmed =~ /^nts\s+enable\b/i) {
            $item->{'type'} = 'nts_enable';
            $item->{'value'} = 1;
        }
        
        push(@rv, $item);
        $line_no++;
    }
    close($fh);
    return \@rv;
}

# save_ntp_config(config_ref)
# Writes the array of hash references back to the configuration file.
sub save_ntp_config {
    my ($conf) = @_;
    my $file = $config{'ntp_conf'} || '/etc/ntpsec/ntp.conf';
    my $temp = $file . ".tmp";
    open(my $fh, ">", $temp) || return 0;
    foreach my $item (@$conf) {
        my $line_str = "";
        if ($item->{'type'} eq 'empty') {
            if (defined($item->{'comment'}) && $item->{'comment'} ne '') {
                $line_str = "# " . $item->{'comment'};
            }
        } elsif ($item->{'type'} eq 'server' || $item->{'type'} eq 'pool' || $item->{'type'} eq 'peer') {
            $line_str = "$item->{'type'} $item->{'address'}";
            if ($item->{'options'}->{'nts'}) { $line_str .= " nts"; }
            if ($item->{'options'}->{'iburst'}) { $line_str .= " iburst"; }
            if ($item->{'options'}->{'prefer'}) { $line_str .= " prefer"; }
            if (defined($item->{'options'}->{'minpoll'}) && $item->{'options'}->{'minpoll'} ne '') {
                $line_str .= " minpoll $item->{'options'}->{'minpoll'}";
            }
            if (defined($item->{'options'}->{'maxpoll'}) && $item->{'options'}->{'maxpoll'} ne '') {
                $line_str .= " maxpoll $item->{'options'}->{'maxpoll'}";
            }
            if (defined($item->{'options'}->{'port'}) && $item->{'options'}->{'port'} ne '') {
                $line_str .= " port $item->{'options'}->{'port'}";
            }
            if (defined($item->{'comment'}) && $item->{'comment'} ne '') {
                $line_str .= " # " . $item->{'comment'};
            }
        } elsif ($item->{'type'} eq 'restrict') {
            $line_str = "restrict $item->{'address'}";
            if (defined($item->{'mask'}) && $item->{'mask'} ne '') {
                $line_str .= " mask $item->{'mask'}";
            }
            if (ref($item->{'flags'}) eq 'ARRAY' && @{$item->{'flags'}}) {
                $line_str .= " " . join(" ", @{$item->{'flags'}});
            }
            if (defined($item->{'comment'}) && $item->{'comment'} ne '') {
                $line_str .= " # " . $item->{'comment'};
            }
        } elsif ($item->{'type'} eq 'driftfile') {
            $line_str = "driftfile $item->{'value'}";
            if (defined($item->{'comment'}) && $item->{'comment'} ne '') {
                $line_str .= " # " . $item->{'comment'};
            }
        } elsif ($item->{'type'} eq 'logfile') {
            $line_str = "logfile $item->{'value'}";
            if (defined($item->{'comment'}) && $item->{'comment'} ne '') {
                $line_str .= " # " . $item->{'comment'};
            }
        } elsif ($item->{'type'} eq 'statsdir') {
            $line_str = "statsdir $item->{'value'}";
            if (defined($item->{'comment'}) && $item->{'comment'} ne '') {
                $line_str .= " # " . $item->{'comment'};
            }
        } elsif ($item->{'type'} eq 'statistics') {
            $line_str = "statistics $item->{'value'}";
            if (defined($item->{'comment'}) && $item->{'comment'} ne '') {
                $line_str .= " # " . $item->{'comment'};
            }
        } elsif ($item->{'type'} eq 'tinker_panic') {
            $line_str = "tinker panic $item->{'value'}";
            if (defined($item->{'comment'}) && $item->{'comment'} ne '') {
                $line_str .= " # " . $item->{'comment'};
            }
        } elsif ($item->{'type'} eq 'nts_cert') {
            $line_str = "nts cert $item->{'value'}";
            if (defined($item->{'comment'}) && $item->{'comment'} ne '') {
                $line_str .= " # " . $item->{'comment'};
            }
        } elsif ($item->{'type'} eq 'nts_key') {
            $line_str = "nts key $item->{'value'}";
            if (defined($item->{'comment'}) && $item->{'comment'} ne '') {
                $line_str .= " # " . $item->{'comment'};
            }
        } elsif ($item->{'type'} eq 'nts_enable') {
            $line_str = "nts enable";
            if (defined($item->{'comment'}) && $item->{'comment'} ne '') {
                $line_str .= " # " . $item->{'comment'};
            }
        } else {
            $line_str = $item->{'value'};
            if (defined($item->{'comment'}) && $item->{'comment'} ne '') {
                $line_str .= " # " . $item->{'comment'};
            }
        }
        print $fh $line_str . "\n";
    }
    close($fh);
    if (!rename($temp, $file)) {
        unlink($temp);
        return 0;
    }
    return 1;
}

# get_ntpq_peers()
# Runs ntpq -p and parses the list of active peers.
sub get_ntpq_peers {
    my $ntpq = $config{'ntpq_path'} || '/usr/bin/ntpq';
    my @peers;
    if (!-x $ntpq) {
        return \@peers;
    }
    my $out = &backquote_command(quotemeta($ntpq) . " -p 2>&1");
    my @lines = split(/\r?\n/, $out);
    
    foreach my $line (@lines) {
        next if ($line =~ /^\s*remote\s+/i);
        next if ($line =~ /^===/);
        next if ($line =~ /^\s*$/);
        
        my $flag = ' ';
        if ($line =~ /^([\*\+\-xo#x])/) {
            $flag = $1;
            $line = substr($line, 1);
        }
        
        $line =~ s/^\s+//;
        my @cols = split(/\s+/, $line);
        if (@cols >= 8) {
            my ($remote, $refid, $st, $type, $when, $poll, $reach, $delay, $offset, $jitter);
            if (@cols == 10) {
                ($remote, $refid, $st, $type, $when, $poll, $reach, $delay, $offset, $jitter) = @cols;
            } elsif (@cols == 9) {
                ($remote, $refid, $st, $when, $poll, $reach, $delay, $offset, $jitter) = @cols;
                $type = 'u'; # default to unicast if type column missing
            } else {
                next;
            }
            
            push(@peers, {
                'flag' => $flag,
                'remote' => $remote,
                'refid' => $refid,
                'st' => $st,
                'type' => $type,
                'when' => $when,
                'poll' => $poll,
                'reach' => $reach,
                'delay' => $delay,
                'offset' => $offset,
                'jitter' => $jitter
            });
        }
    }
    return \@peers;
}

# get_nts_info()
# Runs ntpq -c ntsinfo and parses statistics.
sub get_nts_info {
    my $ntpq = $config{'ntpq_path'} || '/usr/bin/ntpq';
    if (!-x $ntpq) {
        return undef;
    }
    my $out = &backquote_command(quotemeta($ntpq) . " -c ntsinfo 2>&1");
    if ($? != 0 || $out =~ /^\*\*\*/ || $out =~ /invalid/i) {
        return undef;
    }
    my %info;
    my @lines = split(/\r?\n/, $out);
    foreach my $line (@lines) {
        if ($line =~ /^([^:]+):\s*(.*)$/) {
            my $k = $1;
            my $v = $2;
            $k =~ s/^\s+//; $k =~ s/\s+$//;
            $v =~ s/^\s+//; $v =~ s/\s+$//;
            $info{$k} = $v;
        }
    }
    return keys(%info) ? \%info : undef;
}

# get_sys_stats()
# Runs ntpq -c sysstats and parses general system/query statistics.
sub get_sys_stats {
    my $ntpq = $config{'ntpq_path'} || '/usr/bin/ntpq';
    if (!-x $ntpq) {
        return undef;
    }
    my $out = &backquote_command(quotemeta($ntpq) . " -c sysstats 2>&1");
    if ($? != 0 || $out =~ /^\*\*\*/ || $out =~ /invalid/i) {
        return undef;
    }
    my %info;
    my @lines = split(/\r?\n/, $out);
    foreach my $line (@lines) {
        if ($line =~ /^([^:]+):\s*(.*)$/) {
            my $k = lc($1);
            my $v = $2;
            $k =~ s/^\s+//; $k =~ s/\s+$//;
            $v =~ s/^\s+//; $v =~ s/\s+$//;
            $info{$k} = $v;
        }
    }
    return keys(%info) ? \%info : undef;
}

# get_ntp_monstats()
# Runs ntpq -c monstats and parses monitor database stats (client tracking stats).
sub get_ntp_monstats {
    my $ntpq = $config{'ntpq_path'} || '/usr/bin/ntpq';
    if (!-x $ntpq) {
        return undef;
    }
    my $out = &backquote_command(quotemeta($ntpq) . " -c monstats 2>&1");
    if ($? != 0 || $out =~ /^\*\*\*/ || $out =~ /invalid/i) {
        return undef;
    }
    my %info;
    my @lines = split(/\r?\n/, $out);
    foreach my $line (@lines) {
        if ($line =~ /^([^:]+):\s*(.*)$/) {
            my $k = lc($1);
            my $v = $2;
            $k =~ s/^\s+//; $k =~ s/\s+$//;
            $v =~ s/^\s+//; $v =~ s/\s+$//;
            $info{$k} = $v;
        }
    }
    return keys(%info) ? \%info : undef;
}


# get_ntp_mru()
# Runs ntpq -c mrulist and parses recently connected clients.
sub get_ntp_mru {
    my $ntpq = $config{'ntpq_path'} || '/usr/bin/ntpq';
    my @mru;
    if (!-x $ntpq) {
        return \@mru;
    }
    my $out = &backquote_command(quotemeta($ntpq) . " -c mrulist 2>&1");
    if ($? != 0 || $out =~ /^\*\*\*/ || $out =~ /invalid/i) {
        return \@mru;
    }
    my @lines = split(/\r?\n/, $out);
    my @headers;
    foreach my $line (@lines) {
        $line =~ s/^\s+//;
        $line =~ s/\s+$//;
        # Skip comments, progress alerts, and empty lines
        next if ($line eq '' || $line =~ /^===/ || $line =~ /ctrl-c/i || $line =~ /collected/i || $line =~ /processed/i || $line =~ /used/i || $line =~ /^#/);
        
        if (!@headers) {
            # Standardize headers (remote address -> addr)
            $line =~ s/remote\s+address/addr/i;
            $line =~ s/\baddress\b/addr/i;
            my @cols = split(/\s+/, $line);
            @headers = map { lc($_) } @cols;
            next;
        }
        
        my @cols = split(/\s+/, $line);
        my %entry;
        for (my $i=0; $i<@headers; $i++) {
            if ($headers[$i] eq 'addr') {
                # Combine all remaining columns for the address
                $entry{'addr'} = join(" ", @cols[$i..$#cols]);
                last;
            } elsif ($i < @cols) {
                $entry{$headers[$i]} = $cols[$i];
            }
        }
        # Filter out loopback/localhost and upstream servers (rport 123)
        next if ($entry{'addr'} =~ /localhost/i || $entry{'addr'} eq '127.0.0.1' || $entry{'addr'} eq '::1');
        next if (defined($entry{'rport'}) && $entry{'rport'} eq '123');

        push(@mru, \%entry) if ($entry{'addr'});
    }
    my @sorted = sort { ($a->{'lstint'} || 0) <=> ($b->{'lstint'} || 0) } @mru;
    my @sliced = splice(@sorted, 0, 500);
    return \@sliced;
}

# get_ntp_mru_upstreams()
# Returns the count of upstream NTP servers in the MRU table (rport == 123)
sub get_ntp_mru_upstreams {
    my $ntpq = $config{'ntpq_path'} || '/usr/bin/ntpq';
    my $count = 0;
    if (!-x $ntpq) {
        return 0;
    }
    my $out = &backquote_command(quotemeta($ntpq) . " -c mrulist 2>&1");
    if ($? != 0 || $out =~ /^\*\*\*/ || $out =~ /invalid/i) {
        return 0;
    }
    my @lines = split(/\r?\n/, $out);
    my @headers;
    foreach my $line (@lines) {
        $line =~ s/^\s+//;
        $line =~ s/\s+$//;
        next if ($line eq '' || $line =~ /^===/ || $line =~ /ctrl-c/i || $line =~ /collected/i || $line =~ /processed/i || $line =~ /used/i || $line =~ /^#/);
        
        if (!@headers) {
            $line =~ s/remote\s+address/addr/i;
            $line =~ s/\baddress\b/addr/i;
            my @cols = split(/\s+/, $line);
            @headers = map { lc($_) } @cols;
            next;
        }
        
        my @cols = split(/\s+/, $line);
        my %entry;
        for (my $i=0; $i<@headers; $i++) {
            if ($headers[$i] eq 'addr') {
                $entry{'addr'} = join(" ", @cols[$i..$#cols]);
                last;
            } elsif ($i < @cols) {
                $entry{$headers[$i]} = $cols[$i];
            }
        }
        if ($entry{'rport'} eq '123' && $entry{'addr'} !~ /localhost/i && $entry{'addr'} ne '127.0.0.1' && $entry{'addr'} ne '::1') {
            $count++;
        }
    }
    return $count;
}





# get_ntp_status()
# Checks systemd service status. Returns (running_bool, enabled_bool)
sub get_ntp_status {
    my $running = 0;
    my $enabled = 0;
    my $service = $config{'ntp_service'} || 'ntpsec';
    
    my $out = &backquote_command("systemctl is-active " . quotemeta($service) . " 2>&1");
    if ($out =~ /^active/i) {
        $running = 1;
    }
    
    my $boot_out = &backquote_command("systemctl is-enabled " . quotemeta($service) . " 2>&1");
    if ($boot_out =~ /^enabled/i) {
        $enabled = 1;
    }
    
    return ($running, $enabled);
}

# service_action(action)
# Performs start, stop, restart, enable, disable systemd service commands.
sub service_action {
    my ($action) = @_;
    my $service = $config{'ntp_service'} || 'ntpsec';
    my $cmd;
    if ($action eq 'start') {
        $cmd = "systemctl start " . quotemeta($service);
    } elsif ($action eq 'stop') {
        $cmd = "systemctl stop " . quotemeta($service);
    } elsif ($action eq 'restart') {
        $cmd = "systemctl restart " . quotemeta($service);
    } elsif ($action eq 'enable') {
        $cmd = "systemctl enable " . quotemeta($service);
    } elsif ($action eq 'disable') {
        $cmd = "systemctl disable " . quotemeta($service);
    } else {
        return (0, "Invalid action");
    }
    my $out = &backquote_logged($cmd . " 2>&1");
    my $code = $?;
    return ($code == 0, $out);
}

# get_peer_flag_html(flag)
# Converts an NTP peer tally flag into styled HTML badge with description tooltip.
sub get_peer_flag_html {
    my ($flag) = @_;
    return "" if (!defined($flag) || $flag eq ' ' || $flag eq '');
    
    my $title = "";
    my $bg_color = "#777777";
    my $lbl_class = "label-default";
    
    if ($flag eq '*') {
        $title = "System Peer (Current primary synchronization source)";
        $bg_color = "#5cb85c"; # Green
        $lbl_class = "label-success";
    } elsif ($flag eq '+') {
        $title = "Candidate (High-quality backup source)";
        $bg_color = "#5bc0de"; # Blue
        $lbl_class = "label-info";
    } elsif ($flag eq '-') {
        $title = "Outlier (Offset too far from consensus)";
        $bg_color = "#f0ad4e"; # Orange
        $lbl_class = "label-warning";
    } elsif ($flag eq 'o') {
        $title = "PPS Peer (Synchronized via hardware PPS signal)";
        $bg_color = "#777777"; # Grey
        $lbl_class = "label-default";
    } elsif ($flag eq 'x') {
        $title = "Falseticker (Discarded, not trusted)";
        $bg_color = "#d9534f"; # Red
        $lbl_class = "label-danger";
    } elsif ($flag eq '.') {
        $title = "Excess (Discarded, too many sources)";
        $bg_color = "#777777"; # Grey
        $lbl_class = "label-default";
    } else {
        $title = "Status: $flag";
        $bg_color = "#777777"; # Grey
        $lbl_class = "label-default";
    }
    
    return "<span class='label $lbl_class' data-toggle='tooltip' data-container='body' title='$title' style='color:#fff; background-color:$bg_color; padding:2px 6px; border-radius:3px; font-weight:bold; cursor:help;'>$flag</span>";
}

1;
