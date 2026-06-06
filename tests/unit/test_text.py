from typing import Literal, assert_type

from rich.text import Text as RichText

from tulip.text import lto, rto
from tulip.components._types import Text

# str type checks

_ = assert_type(lto("value"), str)

# Rich type checks

_ = assert_type(lto(RichText("value"), ochar=RichText("..")), RichText)
_ = assert_type(lto("value", ochar=RichText("")), Literal["value"] | RichText)
_ = assert_type(rto(RichText("value"), ochar=RichText("..")), RichText)
_ = assert_type(rto(RichText("value")), RichText)

# Tulip type checks

_ = assert_type(lto(Text("value"), ochar=Text("..")), Text)
_ = assert_type(lto("value", ochar=Text("")), Literal["value"] | Text)
_ = assert_type(rto(Text("value"), ochar=Text("..")), Text)
_ = assert_type(rto(Text("value")), Text)
