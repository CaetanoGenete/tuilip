from pathlib import Path
from urllib.parse import quote

import pytest


@pytest.fixture
def snapshot_path(request: pytest.FixtureRequest) -> Path:
    result = Path(request.node.nodeid)  # type: ignore
    result = result.relative_to("tests")
    result = Path("tests", "fixtures", quote(str(result), safe="\\/"))
    result.parent.mkdir(parents=True, exist_ok=True)

    return result
