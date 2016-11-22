from enum import Enum


class BlobCopyOperationState(Enum):
    success = "Success"
    failed = "Failed"
    copying = "Copying"
