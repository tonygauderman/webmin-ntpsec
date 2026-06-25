#!/usr/bin/perl
# edit_restrict.cgi
# Form to list, add, edit access control restrict rules.

use WebminCore;
require './ntpsec-lib.pl';

&ReadParse();

my $idx = $in{'idx'};

if (defined($idx)) {
    # 1. Edit or Add single restrict rule form
    my $item;
    my $title;
    if ($idx eq 'new') {
        $title = $text{'restrict_add'};
    } else {
        $title = $text{'restrict_edit'};
        my $conf = &get_ntp_config();
        $item = $conf->[$idx];
        if (!$item || $item->{'type'} ne 'restrict') {
            &error("Invalid restrict index");
        }
    }
    
    &ui_print_header(undef, $title, "");
    
    print &ui_form_start("save_restrict.cgi", "post");
    print &ui_hidden("idx", $idx);
    print &ui_table_start($text{'restrict_header'}, "width=100%", 2);
    
    # Address Mode: Default or Custom
    my $is_default = (!$item || $item->{'address'} eq 'default') ? 1 : 0;
    my $addr_val = $is_default ? '' : $item->{'address'};
    
    my $custom_html = &ui_textbox("address", $addr_val, 30);
    
    print &ui_table_row($text{'restrict_address'},
        &ui_radio("addr_mode", $is_default ? "default" : "custom", [
            [ "default", $text{'restrict_default'} . "<br>" ],
            [ "custom", $text{'restrict_ip'} . ": " . $custom_html ]
        ])
    );
    
    # Netmask
    my $mask = $item ? $item->{'mask'} : '';
    print &ui_table_row($text{'restrict_mask'},
        &ui_textbox("mask", $mask, 20) . " <span style='color:#666;'>(optional, e.g., 255.255.255.0)</span>"
    );
    
    # Restriction Flags
    my @flags_list = ('kod', 'nomimic', 'nomodify', 'noquery', 'nopeer', 'noserve', 'notrap', 'limited');
    my %has_flag;
    if ($item && ref($item->{'flags'}) eq 'ARRAY') {
        $has_flag{$_} = 1 for (@{$item->{'flags'}});
    }
    
    # Default restrict rule options if creating a new one (usually kod, nomodify, nopeer, noquery, limited are good defaults)
    if ($idx eq 'new') {
        $has_flag{'kod'} = 1;
        $has_flag{'nomodify'} = 1;
        $has_flag{'nopeer'} = 1;
        $has_flag{'noquery'} = 1;
        $has_flag{'limited'} = 1;
    }
    
    my $flags_html = "";
    foreach my $f (@flags_list) {
        my $label = $text{'restrict_flag_' . $f} || $f;
        $flags_html .= &ui_checkbox("flags", $f, "<b>$f</b> - $label", $has_flag{$f}) . "<br>\n";
    }
    print &ui_table_row($text{'restrict_flags'}, $flags_html);
    
    # Comment
    my $comment = $item ? $item->{'comment'} : '';
    print &ui_table_row("Comment",
        &ui_textbox("comment", $comment, 60)
    );
    
    print &ui_table_end();
    print &ui_form_end([ [ undef, $text{'save'} ] ]);
    
    &ui_print_footer("edit_restrict.cgi", $text{'restrict_title'});
} else {
    # 2. List all existing restrict rules
    &ui_print_header(undef, $text{'restrict_title'}, "");
    
    my $conf = &get_ntp_config();
    my @rows;
    foreach my $item (@$conf) {
        if ($item->{'type'} eq 'restrict') {
            my $addr_label = $item->{'address'} eq 'default' ? "Default (All clients)" : $item->{'address'};
            my $addr_link = "<a href='edit_restrict.cgi?idx=$item->{'line'}' style='font-weight:bold;'>$addr_label</a>";
            my $mask_disp = $item->{'mask'} || "None";
            
            my @flags_disp;
            if (ref($item->{'flags'}) eq 'ARRAY' && @{$item->{'flags'}}) {
                @flags_disp = map { "<code style='background-color:#eaeaea; color:#333; padding:2px 5px; border-radius:3px; font-size:0.9em; margin-right:4px;'>$_</code>" } @{$item->{'flags'}};
            }
            my $flags_str = @flags_disp ? join(" ", @flags_disp) : "<i>None (No restrictions)</i>";
            
            my $comment_display = $item->{'comment'} ? "<span style='color:#777; font-style:italic;'># $item->{'comment'}</span>" : "";
            
            push(@rows, [
                &ui_checkbox("d", $item->{'line'}),
                $addr_link,
                $mask_disp,
                $flags_str,
                $comment_display
            ]);
        }
    }
    
    my @headers = (
        "",
        "IP Address / Scope",
        "Netmask",
        "Restriction Flags",
        "Comment"
    );
    
    print "<a href='edit_restrict.cgi?idx=new' style='font-size:1.1em; font-weight:bold; margin-bottom:10px; display:inline-block;'>&oplus; $text{'restrict_add'}</a><br>\n";
    
    if (@rows) {
        print &ui_form_start("delete_restricts.cgi", "post");
        print &ui_columns_table(\@headers, undef, \@rows);
        print &ui_submit($text{'restrict_delete'}, "delete", undef, undef, "class='btn btn-danger'");
        print &ui_form_end();
    } else {
        print "<div class='alert alert-info'>$text{'restrict_none'}</div>\n";
    }
    
    &ui_print_footer("", $text{'index_title'});
}
