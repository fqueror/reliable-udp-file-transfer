class Metadata:
    # TODO Acá va a estar bueno si podemos pasarle un `Operation` y `Protocol`,
    # TODO en lugar de `str`s. Sobre todo porque hay código que trabaja con
    # TODO `Metadata` que se podría simplificar.
    def __init__(self, operation: str, filename: str, protocol: str):
        self.operation = operation
        self.filename = filename
        self.protocol = protocol
