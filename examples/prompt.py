from typing import assert_type

from tuilip.components import prompt
from tuilip.render.rich import loop
from tuilip.render.types import Text

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
