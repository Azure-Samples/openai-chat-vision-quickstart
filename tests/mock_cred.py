from collections.abc import Mapping
from typing import Any, Optional

import azure.core.credentials_async


class MockAzureDeveloperCliCredential(azure.core.credentials_async.AsyncTokenCredential):
    def __init__(
        self,
        *,
        tenant_id: str = "",
        additionally_allowed_tenants: Optional[list[str]] = None,
        process_timeout: int = 10,
    ) -> None:
        pass


# Added as Python 3.13 throws a typing error when using the above code
class MockManagedIdentityCredential(azure.core.credentials_async.AsyncTokenCredential):
    def __init__(
        self, *, client_id: Optional[str] = None, identity_config: Optional[Mapping[str, str]] = None, **kwargs: Any
    ) -> None:
        pass
