class Porta:
    """Representa uma porta como um retângulo colorido."""

    def __init__(self, coordenada_x, coordenada_y, escala_x, escala_y, cor):
        """Guarda o centro, as dimensões e a cor da porta."""
        self.coordenada_x = coordenada_x
        self.coordenada_y = coordenada_y
        self.escala_x = escala_x
        self.escala_y = escala_y
        self.cor = cor

    def obter_coordenadas(self):
        """Devolve o centro onde a porta será desenhada."""
        return (self.coordenada_x, self.coordenada_y)

    def obter_escala(self):
        """Informa a largura e a altura usadas no shader."""
        return (self.escala_x, self.escala_y)
