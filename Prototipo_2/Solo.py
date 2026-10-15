class Solo:
    """Descreve uma faixa horizontal do chão."""

    def __init__(self, coordenada_x, coordenada_y, escala_x, escala_y, cor):
        """Recebe centro, largura, altura e cor da faixa."""
        self.coordenada_x = coordenada_x
        self.coordenada_y = coordenada_y
        self.escala_x = escala_x
        self.escala_y = escala_y
        self.cor = cor

    def obter_coordenadas(self):
        """Devolve a posição em que a faixa será desenhada."""
        return (self.coordenada_x, self.coordenada_y)

    def obter_escala(self):
        """Devolve as dimensões usadas para ampliar o retângulo base."""
        return (self.escala_x, self.escala_y)
