# CoreMediaIO DAL Plugin (Skeleton)

This folder contains a minimal skeleton for a CoreMediaIO DAL plug‑in:
- Info.plist (CMIO bundle type)
- VirtualCamDAL.m: entry point stub (CMIOHardwarePlugInFactory)
- VirtualCamDAL-Bridging-Header.h

Next steps to make it functional:
1) Flesh out CMIOHardwarePlugInInterface with device/stream objects (CMIODeviceID, CMIOStreamID) and real property handling.
2) Expose one virtual device that provides a BGRA video stream (kCVPixelFormatType_32BGRA) and timestamps.
3) Use the bridged symbols `VirtualCam_Start`, `VirtualCam_GetLatestPixelBuffer` from the Swift target to feed frames.
4) Create an Xcode project producing a CMIO bundle. Code sign the bundle with proper entitlements and a Developer ID certificate.
5) Install to `/Library/CoreMediaIO/Plug-Ins/DAL/VirtualCam.plugin` and reboot or restart the media stack.

Note: This is a starting point, not a working virtual camera yet.

References:
- Apple CoreMediaIO Plug-Ins Programming Guide
- Sample: Apple AVCam and community virtual camera examples
