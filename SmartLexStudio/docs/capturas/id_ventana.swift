// Imprime el CGWindowID de la ventana del proceso `pid` cuyo ancho es el indicado (argumentos: pid ancho; se descarta la barra de menus por su altura).
import CoreGraphics
import Foundation
let pid = Int32(CommandLine.arguments[1])!
let ancho = Double(CommandLine.arguments[2])!
let lista = CGWindowListCopyWindowInfo([.optionAll], kCGNullWindowID) as! [[String: Any]]
let propias = lista.filter { ($0[kCGWindowOwnerPID as String] as? Int32) == pid }
func anchoDe(_ w: [String: Any]) -> Double { (w[kCGWindowBounds as String] as! [String: Any])["Width"] as! Double }
func altoDe(_ w: [String: Any]) -> Double { (w[kCGWindowBounds as String] as! [String: Any])["Height"] as! Double }
if let w = propias.first(where: { abs(anchoDe($0) - ancho) < 2 && altoDe($0) > 100 }) { print(w[kCGWindowNumber as String] as! Int) }
