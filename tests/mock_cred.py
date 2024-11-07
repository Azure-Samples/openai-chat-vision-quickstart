from collections.abc import Mapping
from typing import Any

import azure.core.credentials_async


class MockAzureCredential(azure.core.credentials_async.AsyncTokenCredential):
    pass


# Added as Python 3.13 throws a typing error when using the above code
class MockManagedIdentityCredential(azure.core.credentials_async.AsyncTokenCredential):
    def __init__(
        self, *, client_id: str | None = None, identity_config: Mapping[str, str] | None = None, **kwargs: Any
    ) -> None:
        pass
