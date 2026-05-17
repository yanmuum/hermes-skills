# WSL Windows Drive Read-Only Mount

Protect Windows drives (D:, F:, G:, etc.) from accidental deletion/modification via WSL agent tools by mounting them read-only.

## When to Use

The agent has full shell/terminal access, including `rm`, `write_file`, and `cp`. If you want the agent to **read** files on Windows drives but never **delete/modify** them, mount the drives read-only in WSL.

## Immediate Remount (Current Session)

```bash
sudo mount -o remount,ro /mnt/d
sudo mount -o remount,ro /mnt/f
sudo mount -o remount,ro /mnt/g
```

Verify:
```bash
mount | grep "/mnt/[dfg]" | grep -o "ro\|rw"
# Should all show "ro"
```

## Persist Across WSL Restarts

Add to `/etc/fstab`:

```
D: /mnt/d drvfs ro,noatime,uid=1000,gid=1000,metadata,umask=22 0 0
F: /mnt/f drvfs ro,noatime,uid=1000,gid=1000,metadata,umask=22 0 0
G: /mnt/g drvfs ro,noatime,uid=1000,gid=1000,metadata,umask=22 0 0
```

## Make Sudo Mount Passwordless (Optional)

If sudo requires a password (common in WSL), add a sudoers rule so mount commands don't prompt:

```bash
# Create /etc/sudoers.d/mount-nopasswd with:
echo 'yanmuu ALL=(ALL) NOPASSWD: /usr/bin/mount' | sudo tee /etc/sudoers.d/mount-nopasswd
echo 'yanmuu ALL=(ALL) NOPASSWD: /bin/mount' | sudo tee -a /etc/sudoers.d/mount-nopasswd
sudo chmod 440 /etc/sudoers.d/mount-nopasswd
```

⚠️ Only add rules for `mount` — do NOT use `NOPASSWD: ALL`.

## Revert to Read-Write

```bash
sudo mount -o remount,rw /mnt/d
```

Remove the fstab entries if you want it to be rw on next WSL boot.

## Known Limitations

- Only affects WSL-side access — Windows applications can still read/write normally
- Some WSL operations (e.g., `chmod` on Windows files via `metadata` option) fail silently on ro mounts — expected
- Does NOT prevent reading — read-only means no accidental deletion, but all files remain visible
