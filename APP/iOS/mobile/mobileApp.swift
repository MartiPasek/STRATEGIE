//
//  mobileApp.swift
//  mobile
//
//  Created by Jiri Honomichl on 08.06.2026.
//

import SwiftUI

@main
struct mobileApp: App {
    // APNs notifikace potřebují UIApplicationDelegate (SwiftUI ho samo nemá) —
    // registrace tokenu, příjem pushe, skok na obrazovku. Viz PushNotifications.swift.
    @UIApplicationDelegateAdaptor(PushDelegate.self) var pushDelegate

    // PŘÍČINA CHYBY S ODZNAKEM NA IKONĚ (nalezeno a opraveno 24. 8. 2026):
    // `PushDelegate.applicationDidBecomeActive` se u SwiftUI appky s
    // @UIApplicationDelegateAdaptor spolehlivě NEVOLÁ — SwiftUI řídí návrat appky
    // do popředí přes scénu, ne přes starý UIApplicationDelegate. Ověřeno naživo na
    // fyzickém iPhonu (ladicí build, iOS 16.7.16): metoda se nezalogovala ani jednou,
    // přestože appka byla aktivní a uživatel s ní pracoval — srovnání odznaku
    // (`synchronizovatNotifikace`) se proto po návratu do appky nikdy nespustilo
    // a odznak zůstával viset na starém čísle. `scenePhase` je Applem doporučená
    // náhrada přesně pro tenhle případ — funkčně ověřeno (badge se srovnal na
    // skutečný počet a po vyřízení i zhasl).
    @Environment(\.scenePhase) private var scenePhase

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .onChange(of: scenePhase) { novaFaze in
            if novaFaze == .active {
                PushDelegate.shared.synchronizovatNotifikace()
            }
        }
    }
}
