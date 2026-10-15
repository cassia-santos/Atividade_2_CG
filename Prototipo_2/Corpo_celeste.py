class Corpo_celeste:
    """Guarda os dados do disco que representa o sol ou a lua."""

    def __init__(self, coordenada_x, coordenada_y, escala_x, escala_y, cor):
        """Recebe o centro, o tamanho e a cor do corpo celeste."""
        self.coordenada_x = coordenada_x
        self.coordenada_y = coordenada_y
        self.escala_x = escala_x
        self.escala_y = escala_y
        self.cor = cor

    def obter_coordenadas(self):
        """Devolve o centro usado para posicionar o disco."""
        return (self.coordenada_x, self.coordenada_y)

    def obter_escala(self):
        """Devolve os tamanhos horizontal e vertical do disco."""
        return (self.escala_x, self.escala_y)
