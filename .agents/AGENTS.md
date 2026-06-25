# Workflow and Release Rules for webmin-ntpsec

Whenever performing any additional development work on this project, follow this exact workflow:

1. **Create an Issue in GitHub:**
   Before writing any code or making edits, create a new GitHub issue using the `gh issue create` command to track the task.
   
2. **Work on a Local Branch:**
   Create and switch to a separate local Git branch (e.g., `issue-<number>-<description>`) for all changes related to the issue. Do not commit directly to `main`.
   
3. **Manual Testing & Confirmation:**
   After implementing and verifying the changes locally, present the results to the user. Wait for the user's explicit confirmation that manual testing has succeeded.
   
4. **Create PR and Merge:**
   Only after the user's manual testing confirmation, create a Pull Request on GitHub (`gh pr create`) and merge it into `main`.
   
5. **Increment Version:**
   After merging:
   - Ask the user if this release should be a **major**, **minor**, or **patch** version increment.
   - Use their answer to increment the version number appropriately (e.g., from `1.0.0` to `2.0.0` for major, `1.1.0` for minor, or `1.0.1` for patch) in `module.info` and any configuration files.
   - Re-run `build.py` to compile the new version.
   - Create a new GitHub release using `gh release create` attaching the new `.wbm.gz` file.
