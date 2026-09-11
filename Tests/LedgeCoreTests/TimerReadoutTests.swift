import Foundation
import LedgeCore
import Testing

@Suite("What the timer card works out")
struct TimerReadoutTests {

    // MARK: - When it ends

    @Test("The end time is the sum, rounded the way a reader would round it")
    func endsAtRounds() {
        let now = Date(timeIntervalSinceReferenceDate: 0)
        // 4m40s: a reader adds it to the clock and gets the next minute.
        let end = TimerReadout.endsAt(remaining: 280, now: now)
        #expect(end == Date(timeIntervalSinceReferenceDate: 300))
    }

    @Test("It rounds down when the reader would")
    func endsAtRoundsDown() {
        let now = Date(timeIntervalSinceReferenceDate: 0)
        #expect(TimerReadout.endsAt(remaining: 100, now: now)
            == Date(timeIntervalSinceReferenceDate: 120))
        #expect(TimerReadout.endsAt(remaining: 80, now: now)
            == Date(timeIntervalSinceReferenceDate: 60))
    }

    @Test("A timer that has finished has no end time to show")
    func noEndWhenDone() {
        let now = Date(timeIntervalSinceReferenceDate: 0)
        #expect(TimerReadout.endsAt(remaining: 0, now: now) == nil)
        #expect(TimerReadout.endsAt(remaining: -5, now: now) == nil)
        #expect(TimerReadout.endsAt(remaining: .nan, now: now) == nil)
    }

    @Test("Under a minute, the end time says nothing the countdown has not")
    func hidesEndTimeWhenClose() {
        #expect(!TimerReadout.showsEndTime(remaining: 59))
        #expect(TimerReadout.showsEndTime(remaining: 60))
        #expect(TimerReadout.showsEndTime(remaining: 3_600))
        #expect(!TimerReadout.showsEndTime(remaining: .infinity), "nor for nonsense")
    }

    // MARK: - What it offers

    @Test("A fresh install offers the classics")
    func defaultPresets() {
        #expect(TimerReadout.presets(recents: []) == TimerReadout.defaults)
    }

    @Test("What was used last comes first, and the classics fill the rest")
    func recentsLead() {
        #expect(TimerReadout.presets(recents: [12]) == [12, 5, 25])
        #expect(TimerReadout.presets(recents: [12, 90]) == [12, 90, 5])
    }

    @Test("Three, however many recents there are")
    func alwaysThree() {
        #expect(TimerReadout.presets(recents: [1, 2, 3, 4, 5, 6]).count == 3)
        #expect(TimerReadout.presets(recents: [1, 2, 3, 4, 5, 6]) == [1, 2, 3])
    }

    @Test("A length is never offered twice")
    func noDuplicates() {
        #expect(TimerReadout.presets(recents: [25, 25, 5]) == [25, 5, 45])
        let chosen = TimerReadout.presets(recents: [5, 45, 25])
        #expect(Set(chosen).count == chosen.count)
    }

    @Test("Nonsense recents are ignored rather than offered")
    func ignoresNonsense() {
        #expect(TimerReadout.presets(recents: [0, -5]) == TimerReadout.defaults)
    }

    // MARK: - What it opens on

    @Test("The card opens on the last length used")
    func opensOnLastUsed() {
        #expect(TimerReadout.openingLength(recents: [12, 30], focusMinutes: 25) == 12)
    }

    @Test("With no history, it opens on the focus block")
    func opensOnFocusLength() {
        #expect(TimerReadout.openingLength(recents: [], focusMinutes: 50) == 50)
        #expect(TimerReadout.openingLength(recents: [], focusMinutes: 0) == 1, "never zero")
    }
}
