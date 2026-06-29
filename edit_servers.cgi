#!/usr/bin/perl
# edit_servers.cgi
# Form to list, add, edit upstream NTP sources.

use WebminCore;
require './ntpsec-lib.pl';

&ReadParse();

my $idx = $in{'idx'};

if (defined($idx)) {
    # 1. Edit or Add single server/pool/peer form
    my $item;
    my $title;
    if ($idx eq 'new') {
        $title = $text{'servers_add'};
    } else {
        $title = $text{'servers_edit'};
        my $conf = &get_ntp_config();
        $item = $conf->[$idx];
        if (!$item || ($item->{'type'} ne 'server' && $item->{'type'} ne 'pool' && $item->{'type'} ne 'peer')) {
            &error("Invalid server index");
        }
    }
    
    &ui_print_header(undef, $title, "");
    
    print &ui_form_start("save_server.cgi", "post");
    print &ui_hidden("idx", $idx);
    print &ui_table_start($text{'servers_header'}, "width=100%", 2);
    
    # Source type
    my $type = $item ? $item->{'type'} : 'server';
    print &ui_table_row($text{'servers_type'},
        &ui_select("type", $type, [
            [ 'server', $text{'servers_type_server'} ],
            [ 'pool', $text{'servers_type_pool'} ],
            [ 'peer', $text{'servers_type_peer'} ]
        ])
    );
    
    # Address / Hostname
    my $address = $item ? $item->{'address'} : '';
    print &ui_table_row($text{'servers_address'},
        &ui_textbox("address", $address, 40)
    );
    
    # Network Time Security (NTS)
    my $nts = $item ? $item->{'options'}->{'nts'} : 0;
    print &ui_table_row($text{'servers_nts'},
        "<div id='nts-field-container'>" . &ui_yesno_radio("nts", $nts) . "</div>"
    );
    
    # iburst
    my $iburst = $item ? $item->{'options'}->{'iburst'} : 1; # default to yes for new
    print &ui_table_row($text{'servers_iburst'},
        &ui_yesno_radio("iburst", $iburst)
    );
    
    # prefer
    my $prefer = $item ? $item->{'options'}->{'prefer'} : 0;
    print &ui_table_row($text{'servers_prefer'},
        &ui_yesno_radio("prefer", $prefer)
    );
    
    # minpoll
    my $minpoll = $item ? $item->{'options'}->{'minpoll'} : '';
    print &ui_table_row($text{'servers_minpoll'},
        &ui_textbox("minpoll", $minpoll, 5) . " <span style='color:#666;'>(e.g., 4 for 16s, 6 for 64s, leave blank for default)</span>"
    );
    
    # maxpoll
    my $maxpoll = $item ? $item->{'options'}->{'maxpoll'} : '';
    print &ui_table_row($text{'servers_maxpoll'},
        &ui_textbox("maxpoll", $maxpoll, 5) . " <span style='color:#666;'>(e.g., 10 for 1024s, leave blank for default)</span>"
    );
    
    # Comment
    my $comment = $item ? $item->{'comment'} : '';
    print &ui_table_row("Comment",
        &ui_textbox("comment", $comment, 60)
    );
    
    print &ui_table_end();
    
    print <<'JS';
<script type="text/javascript">
function checkNtsSupport() {
    var typeSel = document.getElementsByName('type')[0];
    var ntsField = document.getElementById('nts-field-container');
    if (typeSel && ntsField) {
        var tr = ntsField.closest('tr');
        var yesRadio = ntsField.querySelector('input[value="1"]');
        var noRadio = ntsField.querySelector('input[value="0"]');
        if (typeSel.value === 'pool') {
            if (yesRadio) yesRadio.disabled = true;
            if (noRadio) noRadio.checked = true;
            if (tr) {
                tr.style.opacity = '0.5';
                tr.style.pointerEvents = 'none';
            }
        } else {
            if (yesRadio) yesRadio.disabled = false;
            if (tr) {
                tr.style.opacity = '';
                tr.style.pointerEvents = '';
            }
        }
    }
}
document.addEventListener('DOMContentLoaded', checkNtsSupport);
// Run immediately for SPA/AJAX compatibility
var typeSel = document.getElementsByName('type')[0];
if (typeSel) {
    typeSel.addEventListener('change', checkNtsSupport);
    checkNtsSupport();
}
</script>
JS
    print &ui_form_end([ [ undef, $text{'save'} ] ]);
    
    &ui_print_footer("edit_servers.cgi", $text{'servers_title'});
} else {
    # 2. List all existing servers/pools/peers
    &ui_print_header(undef, $text{'servers_title'}, "");
    
    my $conf = &get_ntp_config();
    my @rows;
    foreach my $item (@$conf) {
        if ($item->{'type'} eq 'server' || $item->{'type'} eq 'pool' || $item->{'type'} eq 'peer') {
            my $type_label = $text{'servers_type_'.$item->{'type'}} || ucfirst($item->{'type'});
            my $address_link = "<a href='edit_servers.cgi?idx=$item->{'line'}' style='font-weight:bold;'>$item->{'address'}</a>";
            my $nts_status = $item->{'options'}->{'nts'} ? "Yes" : "No";
            my $iburst_status = $item->{'options'}->{'iburst'} ? "Yes" : "No";
            my $prefer_status = $item->{'options'}->{'prefer'} ? "Yes" : "No";
            my $minpoll = $item->{'options'}->{'minpoll'} || "Default";
            my $maxpoll = $item->{'options'}->{'maxpoll'} || "Default";
            
            my $comment_display = $item->{'comment'} ? "<span style='color:#777; font-style:italic;'># $item->{'comment'}</span>" : "";
            
            push(@rows, [
                &ui_checkbox("d", $item->{'line'}),
                $address_link,
                $type_label,
                $nts_status,
                $iburst_status,
                $prefer_status,
                "$minpoll / $maxpoll",
                $comment_display
            ]);
        }
    }
    
    my @headers = (
        "",
        $text{'servers_address'},
        $text{'servers_type'},
        $text{'servers_nts'},
        $text{'servers_iburst'},
        $text{'servers_prefer'},
        "minpoll / maxpoll",
        "Comment"
    );
    
    print "<a href='edit_servers.cgi?idx=new' style='font-size:1.1em; font-weight:bold; margin-bottom:10px; display:inline-block;'>&oplus; $text{'servers_add'}</a><br>\n";
    
    if (@rows) {
        print &ui_form_start("delete_servers.cgi", "post");
        print &ui_columns_table(\@headers, undef, \@rows);
        print &ui_submit($text{'servers_delete'}, "delete", undef, undef, "class='btn btn-danger'");
        print &ui_form_end();
    } else {
        print "<div class='alert alert-info'>$text{'servers_none'}</div>\n";
    }
    
    &ui_print_footer("", $text{'index_title'});
}
