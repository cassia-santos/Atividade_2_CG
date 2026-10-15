class Predio:
    """Reúne fachada, porta e posições das janelas de um prédio."""

    def __init__(self, coordenada_x, coordenada_y, escala_x, escala_y, cor, porta):
        """Define a fachada e conserva a porta associada a ela."""
        self.coordenada_x = coordenada_x
        self.coordenada_y = coordenada_y
        self.escala_x = escala_x
        self.escala_y = escala_y
        self.cor = cor
        self.janelas = []  # Cada item guarda x, y e se a janela acende à noite.
        self.porta = porta

    def obter_coordenadas(self):
        """Devolve o centro da fachada na cena."""
        return (self.coordenada_x, self.coordenada_y)

    def obter_escala(self):
        """Devolve largura e altura da fachada."""
        return (self.escala_x, self.escala_y)
