from gi.repository import GObject


class Rule(GObject.Object):
    __gtype_name__ = "PostcardRule"

    def __init__(
        self,
        *,
        id: int,
        account_id: int,
        sender_address: str,
        folder_id: int,
    ) -> None:
        super().__init__()
        self.id: int = id
        self.account_id: int = account_id
        self.sender_address: str = sender_address
        self.folder_id: int = folder_id
