import Foundation
import AVFoundation
#if canImport(AppKit)
import AppKit
#endif

public final class VirtualCam: NSObject {
    private let session = AVCaptureSession()
    private let videoOutput = AVCaptureVideoDataOutput()
    private let queue = DispatchQueue(label: "VirtualCam.Output")
    private var configURL = URL(string: "http://127.0.0.1:8000/api/identity-filter/config")
    private(set) var latestPixelBuffer: CVPixelBuffer?

    public static let shared = VirtualCam()

    public override init() {
        super.init()
    }

    public func start() {
        session.beginConfiguration()
        session.sessionPreset = .high
        if let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front) {
            do {
                let input = try AVCaptureDeviceInput(device: device)
                if session.canAddInput(input) { session.addInput(input) }
            } catch {
                print("VirtualCam: cannot create input:", error)
            }
        }
        if session.canAddOutput(videoOutput) { session.addOutput(videoOutput) }
        videoOutput.setSampleBufferDelegate(self, queue: queue)
        session.commitConfiguration()
        session.startRunning()
    }

    public func stop() { session.stopRunning() }
}

extension VirtualCam: AVCaptureVideoDataOutputSampleBufferDelegate {
    public func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        // TODO: Implement filter pipeline (Metal) reading config from FastAPI
        // For now, this is a skeleton that just consumes frames.
        _ = output
        _ = connection
        if let pb = CMSampleBufferGetImageBuffer(sampleBuffer) {
            latestPixelBuffer = pb
        }
    }
}

// MARK: - C Symbols for DAL Plug-in Bridge
@_cdecl("VirtualCam_Start")
public func VirtualCam_Start() {
    VirtualCam.shared.start()
}

@_cdecl("VirtualCam_Stop")
public func VirtualCam_Stop() {
    VirtualCam.shared.stop()
}

@_cdecl("VirtualCam_GetLatestPixelBuffer")
public func VirtualCam_GetLatestPixelBuffer() -> Unmanaged<CVPixelBuffer>? {
    guard let pb = VirtualCam.shared.latestPixelBuffer else { return nil }
    return Unmanaged.passRetained(pb)
}
