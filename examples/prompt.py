from typing import assert_type

from tuilip.components import prompt
from tuilip.render.rich import render
from tuilip.render.types import Text

try:
    result = render(
        Text("Enter your details: "),
        prompt(),
    )
    assert_type(result, str)

except KeyboardInterrupt:
    pass
else:
    print(f"entered: {result}")
