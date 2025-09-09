// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "VirtualCam",
    platforms: [ .macOS(.v13) ],
    products: [ .library(name: "VirtualCam", type: .dynamic, targets: ["VirtualCam"]) ],
    targets: [
        .target(
            name: "VirtualCam",
            path: "VirtualCam",
            swiftSettings: [ .define("VIRTUAL_CAM") ]
        ),
    ]
)
