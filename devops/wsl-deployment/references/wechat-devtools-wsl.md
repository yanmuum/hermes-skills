# WeChat DevTools + WSL Troubleshooting

## Background

User develops WeChat Mini Programs (小程序) inside WSL, but WeChat DevTools is a Windows-native application. The file dialog doesn't support `\\wsl$` network paths, and the simulator fails with fake AppIDs.

## Reproduction Recipe

1. User has a mini program project at `~/lianping-peach-mp/` in WSL
2. Imports via WeChat DevTools → "导入" → tries to find the WSL folder
3. Native file picker shows no Linux/WSL entry
4. After copying to Desktop and importing, simulator shows "模拟器失败"

## Root Causes Found

### 1. WSL Path Not Accessible in Native File Dialog

Windows-native Win32 file dialogs (the old-style `CFileDialog`, not the UWP picker) cannot enumerate `\\wsl$` SMB shares. The `\\wsl$` mount uses SMB/CIFS protocol, which the file dialog doesn't support.

**Fix:** Copy the project to Windows Desktop first: `cp -r ~/project /mnt/c/Users/<USER>/Desktop/`

### 2. Fake AppID Causes Simulator Failure

`project.config.json` contains:
```json
"appid": "wx0000000000000000"
```

This is a placeholder. The simulator refuses to start with a non-existent AppID.

**Fix:** Re-import with "测试号（小程序）" selected at the AppID prompt, or replace with a real AppID.

## Project Structure Used

The `lianping-peach-mp` project at the time:
- Standard WeChat Mini Program structure (pages, components, images, utils, services, subpackages)
- app.json with 8 pages + 2 subpackages (promotion, source-trace)
- TabBar with 4 tabs: home, category, cart, user
- project.config.json with libVersion 3.7.2
- Project name: 连平鹰嘴蜜桃
- Fake AppID: wx0000000000000000
- Windows user: Administrator
- WSL path: /home/yanmuu/lianping-peach-mp/
- Desktop copy: C:\Users\Administrator\Desktop\lianping-peach-mp\
