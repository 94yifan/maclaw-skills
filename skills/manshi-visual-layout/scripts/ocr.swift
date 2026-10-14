import Foundation
import Vision
import AppKit
let path = CommandLine.arguments[1]
guard let img = NSImage(contentsOfFile: path), let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { exit(1) }
let req = VNRecognizeTextRequest { r, _ in
  guard let obs = r.results as? [VNRecognizedTextObservation] else { return }
  for o in obs {
    if let t = o.topCandidates(1).first {
      let b = o.boundingBox
      print(String(format: "%.3f %.3f %.3f %.3f", b.origin.x, b.origin.y, b.size.width, b.size.height), "|", t.string)
    }
  }
}
req.recognitionLanguages = ["zh-Hans","en-US"]
req.recognitionLevel = .accurate
let h = VNImageRequestHandler(cgImage: cg, options: [:])
try? h.perform([req])
