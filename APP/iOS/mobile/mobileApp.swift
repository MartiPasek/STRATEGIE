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

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
