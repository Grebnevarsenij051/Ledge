import Foundation

/// The two things the timer card has to work out rather than simply draw:
/// when a countdown will end, and which lengths to offer before one starts.
///
/// Pure, so both can be checked against awkward cases — a timer that ends
/// after midnight, a run of recents long enough to crowd out every default —
/// rather than by watching the card and hoping.
public enum TimerReadout {

    /// When a running countdown will finish.
    ///
    /// Rounded to the minute it will *show*: a card reading "Ends at 3:42"
    /// beside 4 minutes 40 seconds remaining is not wrong by the clock, but it
    /// is wrong to a reader, who adds the two and gets 3:43. Rounding the sum
    /// the way the reader would makes the two numbers agree.
    public static func endsAt(remaining: TimeInterval, now: Date) -> Date? {
        guard remaining.isFinite, remaining > 0 else { return nil }
        let end = now.addingTimeInterval(remaining)
        let seconds = end.timeIntervalSinceReferenceDate
        return Date(timeIntervalSinceReferenceDate: (seconds / 60).rounded() * 60)
    }

    /// Whether the end time is worth showing.
    ///
    /// Under a minute it says nothing the countdown has not already said, and
    /// it would change under the reader's eyes as the rounding flips.
    public static func showsEndTime(remaining: TimeInterval) -> Bool {
        remaining.isFinite && remaining >= 60
    }

    /// The lengths offered on the ready card, freshest first.
    ///
    /// Three, not five: a row of chips is a menu, and a menu of five is read
    /// rather than recognised. What the user has actually used comes first,
    /// and the classics fill whatever is left — so the card is familiar on the
    /// first day and personal by the second.
    public static func presets(recents: [Int], slots: Int = 3) -> [Int] {
        var chosen: [Int] = []
        for minutes in recents where minutes > 0 && !chosen.contains(minutes) {
            chosen.append(minutes)
            if chosen.count == slots { return chosen }
        }
        for fallback in defaults where !chosen.contains(fallback) {
            chosen.append(fallback)
            if chosen.count == slots { return chosen }
        }
        return chosen
    }

    /// The lengths a timer offers before it knows anything about its user:
    /// a short one, a working block, and a long one.
    public static let defaults = [5, 25, 45]

    /// The length a fresh ready card opens on, and what Start would use.
    public static func openingLength(recents: [Int], focusMinutes: Int) -> Int {
        // What they used last, or the length of their focus block — which is
        // the only other number on this card the user has ever chosen.
        recents.first { $0 > 0 } ?? max(1, focusMinutes)
    }
}
