# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Scenario:
    id: str
    label: Literal["predator", "benign"]
    conversation: tuple[str, ...]
    actor_tier: int
    expected_tier_after_honeypot: int


def _predator(id_: str, *lines: str) -> Scenario:
    return Scenario(
        id=id_,
        label="predator",
        conversation=lines,
        actor_tier=4,
        expected_tier_after_honeypot=5,
    )


def _benign(id_: str, *lines: str) -> Scenario:
    return Scenario(
        id=id_,
        label="benign",
        conversation=lines,
        actor_tier=4,
        expected_tier_after_honeypot=4,
    )


PREDATOR_SCENARIOS: tuple[Scenario, ...] = (
    _predator(
        "p01", "actor: hey can we keep this just between us", "actor: don't tell your mom we talk"
    ),
    _predator(
        "p02",
        "actor: let's move off this app, what's your snap",
        "actor: i know a quieter place we can chat",
    ),
    _predator(
        "p03",
        "actor: you're so mature for your age",
        "actor: i've never connected with anyone like this",
    ),
    _predator("p04", "actor: send me a selfie", "actor: just one, i promise i won't share"),
    _predator(
        "p05", "actor: what's your address", "actor: i'd love to send you something in the mail"
    ),
    _predator(
        "p06", "actor: here's $50 on venmo as a gift", "actor: consider it our little secret"
    ),
    _predator("p07", "actor: are you alone right now", "actor: is anyone else home"),
    _predator("p08", "actor: your parents don't understand you the way i do"),
    _predator(
        "p09", "actor: have you ever had a boyfriend", "actor: can you keep a secret about us"
    ),
    _predator("p10", "actor: delete these messages after you read them"),
    _predator(
        "p11",
        "actor: we have a special connection",
        "actor: you're different from other kids i've met",
    ),
    _predator("p12", "actor: what's your school name", "actor: i might be in the area next week"),
    _predator("p13", "actor: you can tell me anything", "actor: i'll never judge you"),
    _predator("p14", "actor: i'd love to see what you look like in your school uniform"),
    _predator(
        "p15",
        "actor: you're the only person who gets me",
        "actor: promise me you'll keep talking to me",
    ),
    _predator("p16", "actor: switch to discord, less people watching there"),
    _predator("p17", "actor: what time do you go to sleep", "actor: i'll stay up with you"),
    _predator("p18", "actor: don't post this conversation", "actor: people wouldn't understand"),
    _predator(
        "p19",
        "actor: have you ever been kissed",
        "actor: that's something grown-ups shouldn't know you're asking about",
    ),
    _predator(
        "p20", "actor: i know you're older than 13 really", "actor: you can trust me with that"
    ),
    _predator(
        "p21", "actor: what's your real phone number", "actor: i'll call you so we can really talk"
    ),
    _predator(
        "p22", "actor: come over to my place this weekend", "actor: my friends won't be there"
    ),
    _predator("p23", "actor: here's a new account, add me there instead"),
    _predator("p24", "actor: do you have a webcam", "actor: turn it on for me quickly"),
    _predator("p25", "actor: you're my best friend", "actor: can we meet irl"),
    _predator("p26", "actor: i bought you a gift card", "actor: don't tell anyone it was from me"),
    _predator(
        "p27", "actor: if you tell anyone i'll stop talking to you", "actor: this is just our thing"
    ),
    _predator("p28", "actor: your body is so developed for your age"),
    _predator("p29", "actor: what do you wear to bed"),
    _predator(
        "p30", "actor: you deserve better than the friends you have", "actor: i'll always be here"
    ),
)


BENIGN_SCENARIOS: tuple[Scenario, ...] = (
    _benign(
        "b01",
        "actor: happy birthday! i sent you a gift card for your gaming",
        "actor: your mom said it was ok",
    ),
    _benign("b02", "actor: great job on the school project", "actor: proud of you"),
    _benign("b03", "actor: joking — you're killing it at minecraft lol"),
    _benign("b04", "actor: we should all hang out after school"),
    _benign("b05", "actor: did you finish the homework", "actor: can you send a pic of page 3"),
    _benign("b06", "actor: have fun at soccer practice today"),
    _benign("b07", "actor: my dog did the funniest thing, wanna see a video"),
    _benign("b08", "actor: happy birthday buddy, can we do cake at your place"),
    _benign("b09", "actor: my son says you're the best chess player in class"),
    _benign("b10", "actor: dad here — remember to take your meds"),
    _benign("b11", "actor: don't forget your lunchbox at school"),
    _benign("b12", "actor: the teacher said the field trip is saturday"),
    _benign("b13", "actor: we are doing a surprise party for mom, keep it quiet"),
    _benign("b14", "actor: i brought extra snacks for the team"),
    _benign("b15", "actor: good luck at the piano recital tonight"),
    _benign("b16", "actor: your aunt is coming to visit this weekend"),
    _benign("b17", "actor: grandma sent you a card in the mail"),
    _benign("b18", "actor: do you want to go to the library with me"),
    _benign("b19", "actor: soccer practice is cancelled, coach emailed"),
    _benign("b20", "actor: big sis here, want me to grab you a snack"),
)


ALL_SCENARIOS: tuple[Scenario, ...] = PREDATOR_SCENARIOS + BENIGN_SCENARIOS
