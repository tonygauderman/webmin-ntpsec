#!/usr/bin/env python3
# build.py
# Packages the Webmin NTPsec module into a standard ntpsec.wbm.gz distribution file.

import os
import shutil
import tarfile

def build():
    workspace = '/Users/tonygauderman/Antigravity/webmin-ntpsec'
    build_temp = os.path.join(workspace, 'build_temp')
    ntpsec_dir = os.path.join(build_temp, 'ntpsec')
    
    print("Preparing package layout...")
    # Clean and recreate temporary build directories
    if os.path.exists(build_temp):
        shutil.rmtree(build_temp)
    os.makedirs(ntpsec_dir)
    
    # List of files and folders to package
    files_to_copy = [
        'module.info', 'config', 'config.info', 'ntpsec-lib.pl',
        'index.cgi', 'edit_servers.cgi', 'save_server.cgi', 'delete_servers.cgi',
        'edit_restrict.cgi', 'save_restrict.cgi', 'delete_restricts.cgi',
        'edit_misc.cgi', 'save_misc.cgi', 'edit_manual.cgi', 'save_manual.cgi',
        'action.cgi', 'sync.cgi', 'status_ajax.cgi'
    ]
    dirs_to_copy = ['lang', 'images']
    
    # Copy files
    for f in files_to_copy:
        src = os.path.join(workspace, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(ntpsec_dir, f))
            # Set executable permissions for scripts
            if f.endswith('.cgi'):
                os.chmod(os.path.join(ntpsec_dir, f), 0o755)
            else:
                os.chmod(os.path.join(ntpsec_dir, f), 0o644)
        else:
            print(f"Warning: File {f} not found, skipping.")
            
    # Copy directories
    for d in dirs_to_copy:
        src = os.path.join(workspace, d)
        if os.path.exists(src):
            dest = os.path.join(ntpsec_dir, d)
            shutil.copytree(src, dest)
            # Ensure proper permissions inside directories
            for root, subdirs, files in os.walk(dest):
                for sd in subdirs:
                    os.chmod(os.path.join(root, sd), 0o755)
                for file in files:
                    os.chmod(os.path.join(root, file), 0o644)
                    
    output_filename = os.path.join(workspace, 'ntpsec.wbm.gz')
    print(f"Creating archive {output_filename}...")
    
    # Create gzipped tar archive with 'ntpsec' as the root directory
    original_cwd = os.getcwd()
    try:
        os.chdir(build_temp)
        with tarfile.open(output_filename, 'w:gz') as tar:
            tar.add('ntpsec')
    finally:
        os.chdir(original_cwd)
        
    # Clean up temp files
    shutil.rmtree(build_temp)
    print("Build complete! ntpsec.wbm.gz generated successfully.")

if __name__ == '__main__':
    build()
    
