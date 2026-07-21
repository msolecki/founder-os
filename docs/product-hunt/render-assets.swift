#!/usr/bin/env swift

import AppKit
import Foundation

struct Asset {
    let stem: String
    let width: Int
    let height: Int
}

let assets = [
    Asset(stem: "thumbnail-240", width: 240, height: 240),
    Asset(stem: "gallery-01-outcome", width: 1270, height: 760),
    Asset(stem: "gallery-02-onboarding", width: 1270, height: 760),
    Asset(stem: "gallery-03-trust", width: 1270, height: 760),
    Asset(stem: "gallery-04-operating-loop", width: 1270, height: 760),
]

let fileManager = FileManager.default
let launchDirectory = URL(fileURLWithPath: fileManager.currentDirectoryPath)
    .appendingPathComponent("docs/product-hunt", isDirectory: true)

for asset in assets {
    let source = launchDirectory
        .appendingPathComponent("sources", isDirectory: true)
        .appendingPathComponent("\(asset.stem).svg")
    let destination = launchDirectory.appendingPathComponent("\(asset.stem).png")

    guard let image = NSImage(contentsOf: source) else {
        fatalError("Could not load \(source.path)")
    }
    guard let bitmap = NSBitmapImageRep(
        bitmapDataPlanes: nil,
        pixelsWide: asset.width,
        pixelsHigh: asset.height,
        bitsPerSample: 8,
        samplesPerPixel: 4,
        hasAlpha: true,
        isPlanar: false,
        colorSpaceName: .deviceRGB,
        bytesPerRow: 0,
        bitsPerPixel: 0
    ) else {
        fatalError("Could not allocate bitmap for \(asset.stem)")
    }

    NSGraphicsContext.saveGraphicsState()
    guard let context = NSGraphicsContext(bitmapImageRep: bitmap) else {
        fatalError("Could not create graphics context for \(asset.stem)")
    }
    NSGraphicsContext.current = context
    context.imageInterpolation = .high
    image.draw(
        in: NSRect(x: 0, y: 0, width: asset.width, height: asset.height),
        from: .zero,
        operation: .copy,
        fraction: 1
    )
    context.flushGraphics()
    NSGraphicsContext.restoreGraphicsState()

    guard let png = bitmap.representation(using: .png, properties: [:]) else {
        fatalError("Could not encode \(asset.stem)")
    }
    try png.write(to: destination, options: .atomic)
    print("rendered \(destination.lastPathComponent): \(asset.width)x\(asset.height)")
}
