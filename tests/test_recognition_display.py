from pricetyper.ui.recognition_display import RecognitionDisplay


def test_partial_text_is_not_shown_as_final_or_as_a_price_candidate():
    display = RecognitionDisplay()

    display.on_asr("partial", "xã tăng")
    display.on_candidate("partial", 300)

    assert display.final_text == "—"
    assert display.partial_text == "xã tăng"
    assert display.provisional_candidate == "300"
    assert display.candidate == "—"


def test_partial_without_price_clears_only_the_provisional_candidate():
    display = RecognitionDisplay()
    display.on_candidate("final", 199000)

    display.on_candidate("partial", 300000)
    assert display.provisional_candidate == "300000"
    assert display.candidate == "199000"

    display.on_candidate("partial", None)
    assert display.provisional_candidate == "—"
    assert display.candidate == "199000"


def test_final_text_and_candidate_replace_the_temporary_values():
    display = RecognitionDisplay()
    display.on_asr("partial", "ba trăm")
    display.on_candidate("partial", 300)

    display.on_asr("final", "giá ba trăm nghìn")
    display.on_candidate("final", 300)

    assert display.final_text == "giá ba trăm nghìn"
    assert display.partial_text == "—"
    assert display.provisional_candidate == "—"
    assert display.candidate == "300"
