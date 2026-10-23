package com.pricetyper.android

import java.text.Normalizer
import java.util.Locale

/** Number-first Vietnamese parser ported from src/pricetyper/parsing/vi_number.py. */
internal object VietnameseNumberParser {
    private val lead = mapOf(
        "một" to 1, "hai" to 2, "ba" to 3, "bốn" to 4, "năm" to 5,
        "sáu" to 6, "bảy" to 7, "bẩy" to 7, "tám" to 8, "chín" to 9,
    )
    private val onesOnly = mapOf("mốt" to 1, "tư" to 4, "lăm" to 5, "nhăm" to 5)
    private val digits = lead + onesOnly + mapOf("không" to 0)
    private val tens = setOf("mươi", "chục")
    private val zeroConnectors = setOf("linh", "lẻ")
    private val thousands = setOf("nghìn", "ngàn")
    private val kTokens = setOf("k", "ca", "ka")
    private val numberWords = digits.keys + setOf("mười", "trăm", "rưỡi") + tens + zeroConnectors + thousands
    private val groupedArabic = Regex("(?<![0-9])([0-9]{1,3}(?:[.,][0-9]{3})+)(k?)(?![0-9])")
    private val arabic = Regex("^([0-9]{1,12})(k?)$")
    private data class Core(
        val value: Long,
        val end: Int,
        val kind: String,
        val digits: String,
        val unit: Boolean,
    )

    private fun tokenize(raw: String): List<String> {
        var text = Normalizer.normalize(raw.lowercase(Locale.ROOT), Normalizer.Form.NFC)
        text = groupedArabic.replace(text) { match ->
            match.groupValues[1].replace(".", "").replace(",", "") + match.groupValues[2]
        }
        return buildString(text.length) {
            text.forEach { append(if (it.isLetterOrDigit() || it.isWhitespace()) it else ' ') }
        }.trim().split(Regex("\\s+")).filter(String::isNotEmpty)
    }

    private fun isNumber(token: String): Boolean =
        token in numberWords || arabic.matches(token)

    private fun digit(tokens: List<String>, index: Int): Int? =
        tokens.getOrNull(index)?.let(digits::get)

    private fun afterHundred(tokens: List<String>, index: Int, shorthand: Boolean): Pair<Long, Int> {
        if (index >= tokens.size) return 0L to index
        val word = tokens[index]
        if (word == "rưỡi") return 50L to index + 1
        if (word == "mốt") return (if (shorthand) 10L else 1L) to index + 1
        if (word in zeroConnectors) {
            val value = digit(tokens, index + 1)
            return if (value != null && value != 0) value.toLong() to index + 2 else 0L to index
        }
        if (word == "mười") {
            val value = digit(tokens, index + 1)
            return if (value != null) (10 + value).toLong() to index + 2 else 10L to index + 1
        }
        if (word in lead && (lead[word] ?: 0) >= 2 && tokens.getOrNull(index + 1) in tens) {
            val base = (lead[word] ?: 0) * 10
            val value = digit(tokens, index + 2)
            return if (value != null) (base + value).toLong() to index + 3 else base.toLong() to index + 2
        }
        if (word in lead || word == "không") {
            val first = digits[word] ?: 0
            val second = digit(tokens, index + 1)
            if (second != null) return (first * 10 + second).toLong() to index + 2
            if (word in lead) return (if (shorthand) first * 10L else first.toLong()) to index + 1
        }
        return 0L to index
    }

    private fun readCore(tokens: List<String>, index: Int, shorthand: Boolean): Core? {
        if (index >= tokens.size) return null
        val token = tokens[index]
        val arabicMatch = arabic.matchEntire(token)
        if (arabicMatch != null) {
            val raw = arabicMatch.groupValues[1]
            val value = raw.toLongOrNull() ?: return null
            val hasK = arabicMatch.groupValues[2].isNotEmpty()
            return Core(if (hasK) value * 1000 else value, index + 1, "arabic", raw, hasK)
        }
        if (token in lead && tokens.getOrNull(index + 1) == "trăm") {
            val (tail, end) = afterHundred(tokens, index + 2, shorthand)
            return Core((lead[token] ?: 0) * 100L + tail, end, "positional", "", false)
        }
        if (token == "trăm" && (index == 0 || (!isNumber(tokens[index - 1]) && tokens[index - 1] != "phần"))) {
            val (tail, end) = afterHundred(tokens, index + 1, shorthand)
            return Core(100L + tail, end, "positional", "", false)
        }
        if (token == "mười") {
            val value = digit(tokens, index + 1)
            return if (value != null) Core((10 + value).toLong(), index + 2, "positional", "", false)
            else Core(10L, index + 1, "positional", "", false)
        }
        if (token in lead && (lead[token] ?: 0) >= 2 && tokens.getOrNull(index + 1) in tens) {
            val base = (lead[token] ?: 0) * 10
            val value = digit(tokens, index + 2)
            return if (value != null) Core((base + value).toLong(), index + 3, "positional", "", false)
            else Core(base.toLong(), index + 2, "positional", "", false)
        }
        if (token in lead) {
            val result = StringBuilder().append(lead[token])
            var end = index + 1
            while (end < tokens.size && digits.containsKey(tokens[end]) && result.length < 4) {
                if (tokens.getOrNull(end + 1) == "trăm" || tokens.getOrNull(end + 1) in tens) break
                result.append(digits[tokens[end]])
                end++
            }
            val digitText = result.toString()
            return Core(digitText.toLong(), end, if (digitText.length > 1) "digits" else "positional", if (digitText.length > 1) digitText else "", false)
        }
        return null
    }

    private fun readCountSequence(tokens: List<String>, index: Int): Pair<List<Int>, Int>? {
        if (tokens.getOrNull(index) != "một") return null
        val result = mutableListOf<Int>()
        var cursor = index
        var expected = 1
        while (cursor < tokens.size && lead[tokens[cursor]] == expected) {
            result += expected
            cursor++
            expected++
        }
        if (result.size < 2) return null
        if (tokens.getOrNull(cursor)?.let { isNumber(it) || it in kTokens } == true) return null
        return result to cursor
    }

    fun parseAll(text: String, shorthand: Boolean = true, splitCountSequence: Boolean = true): List<Long> {
        val tokens = tokenize(text)
        val output = mutableListOf<Long>()
        var index = 0
        while (index < tokens.size) {
            if (splitCountSequence) {
                val sequence = readCountSequence(tokens, index)
                if (sequence != null) {
                    output += sequence.first.map(Int::toLong)
                    index = sequence.second
                    continue
                }
            }
            val core = readCore(tokens, index, shorthand)
            if (core == null) {
                index++
                continue
            }
            var value = core.value
            var end = core.end
            if (tokens.getOrNull(end) in kTokens) {
                value *= 1000
                end++
            } else if (tokens.getOrNull(end) in thousands) {
                end++
                if (tokens.getOrNull(end)?.let(::isNumber) == true) {
                    val following = readCore(tokens, end, shorthand)
                    val followingHasUnit = following != null && (following.unit || tokens.getOrNull(following.end) in (thousands + kTokens))
                    if (!followingHasUnit) {
                        while (tokens.getOrNull(end)?.let(::isNumber) == true) end++
                        index = end
                        continue
                    }
                }
                value *= 1000
            }
            // This function is called on VAD-final ASR segments; the segment boundary closes the span.
            output += value
            index = end
        }
        return output
    }
}
