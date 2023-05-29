class AddressError(ValueError):
    def __init__(
        self,
        message: str,
        section: str,
        virtual_address: int = None,
        raw_address: int = None,
    ) -> None:
        self.message = message
        self.section = section
        self.virtual_address = virtual_address
        self.raw_address = raw_address
