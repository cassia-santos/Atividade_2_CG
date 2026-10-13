class Porta:
    
    def __init__(self, coordenada_x, coordenada_y, escala_x, escala_y, cor):
        self.coordenada_x = coordenada_x
        self.coordenada_y = coordenada_y
        self.escala_x = escala_x
        self.escala_y = escala_y
        self.cor = cor
        
    def obter_coordenadas(self):
        return(self.coordenada_x, self.coordenada_y)
    
    def obter_escala(self):
        return(self.escala_x, self.escala_y)