from typing import assert_type

from tulip.components import prompt
from tulip.render.rich import loop
from tulip.render.types import Text

try:
    result = loop(
        Text("Enter your details: "),
        prompt(),
    )
    assert_type(result, str)

except KeyboardInterrupt:
    pass
else:
    print(f"entered: {result}")
