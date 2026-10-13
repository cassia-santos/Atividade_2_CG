"""
Senhor Coracao: uma geometria desenhada varias vezes.

Duas curvas na VRAM (o coracao e um circulo) e cinco desenhos por quadro. O que
muda de um desenho para o outro nao esta em nenhum VBO: esta em variaveis
uniformes. As teclas nao animam nada -- elas trocam o valor de uma uniforme, e
o desenho seguinte ja sai diferente.

MCCC007-23 - Computacao Grafica - UFABC

Executar: python 06_senhor_coracao.py
Teclas:   SETAS movem o olhar | D alterna dia/noite | ESC sai
"""
import sys
from pathlib import Path

import glfw
import moderngl
import numpy as np

#Importando as classes
from Porta import Porta
from Predio import Predio
from Solo import Solo
from Corpo_celeste import Corpo_celeste

SHADERS = Path(__file__).parent / "shaders"

CINZA_ESCURO = (0.2, 0.2, 0.2, 1.0) 
CINZA_CLARO = (0.6, 0.6, 0.6, 1.0)
CINZA_3 = (0.4, 0.4, 0.4, 1.0)
CINZA_4 = (0.5, 0.5, 0.5, 1.0)
AMARELO = (1.0, 1.0, 0.0, 1.0)
MAGENTA = (0.85, 0.10, 0.45, 1.0)
BRANCO = (1.0, 1.0, 1.0, 1.0)
PRETO = (0.05, 0.05, 0.05, 1.0)
FUNDO_DIA = (0.67, 0.84, 0.9, 1.0)
FUNDO_NOITE = (0.05, 0.05, 0.12, 1.0)

ESCALA_CORPO = (0.62, 0.62)
ESCALA_OLHO, ESCALA_PUPILA = (0.085, 0.085), (0.040, 0.040)
CENTRO_OLHO = (0.17, 0.20)   # afastamento do eixo e altura de cada olho

# Ate onde a pupila pode sair do centro do olho, sem escapar do branco.
LIMITE_OLHAR = ESCALA_OLHO[0] - ESCALA_PUPILA[0]
PASSO_OLHAR = LIMITE_OLHAR / 2.0


def leque(x, y):
    """Empacota uma curva fechada como TRIANGLE_FAN: primeiro o centro, depois
    a curva, e o primeiro ponto repetido no fim para fechar a volta."""
    x = np.concatenate(([0.0], x, [x[0]]))
    y = np.concatenate(([0.0], y, [y[0]]))
    return np.column_stack((x, y, np.zeros_like(x), np.ones_like(x))).astype('f4')


def curva_coracao(n=180):
    t = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    x = 16.0 * np.sin(t) ** 3
    y = (13.0 * np.cos(t) - 5.0 * np.cos(2 * t)
         - 2.0 * np.cos(3 * t) - np.cos(4 * t))
    y = y - 0.5 * (y.max() + y.min())      # centra a curva na origem
    return leque(x / 17.0, y / 17.0)       # normaliza para caber em [-1, 1]


def curva_circulo(n=48):
    t = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    return leque(np.cos(t), np.sin(t))

def curva_retangulo():
    return np.array([
        -0.5, -0.5, 0.0, 1.0,      
         0.5, -0.5, 0.0, 1.0,      
         0.5,  0.5, 0.0, 1.0,      
        -0.5,  0.5, 0.0, 1.0,
        ], dtype='f4')

def indices_retangulo():
    return np.array([0, 1, 2,  2, 3, 0], dtype ='u4')

def erro_glfw(codigo, descricao):
    """Substitui o aviso padrÃ£o do pyGLFW: imprime cÃ³digo 
    e descriÃ§Ã£o de qualquer erro do GLFW em stderr"""
    print(f"GLFW [{codigo}]: {descricao}", file=sys.stderr)


glfw.set_error_callback(erro_glfw)   # antes de glfw.init(), de proposito

if not glfw.init():
    sys.exit("FALHA: glfw nao inicializou")

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 0)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
# Sem a dica acima, o macOS recusa qualquer contexto 3.2+ e
# create_window devolve None. E inofensiva no Windows e no Linux.
glfw.window_hint(glfw.SAMPLES, 4)        # quatro amostras por pixel
glfw.window_hint(glfw.RESIZABLE, False)  # janela quadrada: ver a nota

janela = glfw.create_window(640, 640, "Senhor Coracao", None, None)
if not janela:
    glfw.terminate()
    sys.exit("FALHA: nao foi possivel criar a janela")

glfw.make_context_current(janela)
ctx = moderngl.create_context()

# SAMPLES e uma dica, nao uma garantia: o driver pode entregar menos amostras
# do que se pediu. Conferir e barato.
print(f"amostras por pixel obtidas: {ctx.screen.samples}")

prog = ctx.program(
    vertex_shader=(SHADERS / "senhor_coracao.vert").read_text(encoding="utf-8"),
    fragment_shader=(SHADERS / "senhor_coracao.frag").read_text(encoding="utf-8"),
)


def montar(vertices, ebo):
    vbo = ctx.buffer(vertices.tobytes())
    if ebo is None:
        vao = ctx.vertex_array(prog, [(vbo, '4f', 'vPosition')])
    else:
        vao = ctx.vertex_array(prog, [(vbo, '4f', 'vPosition')], index_buffer = ebo)
        
    return vbo, vao

ebo_retangulo = ctx.buffer(indices_retangulo().tobytes())

vbo_coracao, vao_coracao = montar(curva_coracao(), None)
vbo_circulo, vao_circulo = montar(curva_circulo(), None)
vbo_retangulo, vao_retangulo = montar(curva_retangulo(), ebo_retangulo)

# Todo o estado do programa cabe em dois numeros e um booleano.
olhar_x, olhar_y = 0.0, 0.0
noite = False


def tecla(window, key, scancode, action, mods):
    global olhar_x, olhar_y, noite
    if action != glfw.PRESS and action != glfw.REPEAT:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)
    elif key == glfw.KEY_D:
        noite = not noite
    elif key in (glfw.KEY_LEFT, glfw.KEY_RIGHT, glfw.KEY_UP, glfw.KEY_DOWN):
        dx = {glfw.KEY_LEFT: -1.0, glfw.KEY_RIGHT: 1.0}.get(key, 0.0)
        dy = {glfw.KEY_DOWN: -1.0, glfw.KEY_UP: 1.0}.get(key, 0.0)
        olhar_x += dx * PASSO_OLHAR
        olhar_y += dy * PASSO_OLHAR
        # O branco do olho e um CIRCULO, entao o limite tem de ser no vetor.
        # Limitar cada eixo em separado prende a pupila num quadrado, e na
        # diagonal ela escapa: o centro chega a 0.064 do centro do olho e a
        # borda da pupila a 0.104, contra um raio de 0.085.
        distancia = (olhar_x ** 2 + olhar_y ** 2) ** 0.5
        if distancia > LIMITE_OLHAR:
            olhar_x *= LIMITE_OLHAR / distancia
            olhar_y *= LIMITE_OLHAR / distancia


glfw.set_key_callback(janela, tecla)


def ajustar(nome, valor):
    """Escreve num uniforme, se ele existir.

    Um uniforme que o shader deixa de usar e descartado pelo ligador do
    GLSL, e prog[nome] levantaria KeyError. Os experimentos do capitulo
    fazem exatamente isso -- ignorar u_cor, ignorar u_atenuacao -- entao
    o acesso passa todo por aqui.
    """
    uniforme = prog.get(nome, None)
    if uniforme is not None:
        uniforme.value = valor


def desenhar(vao, escala, deslocamento, cor, primitiva):
    """Carrega os tres uniformes daquele desenho e dispara a chamada."""
    ajustar('u_escala', escala)
    ajustar('u_deslocamento', deslocamento)
    ajustar('u_cor', cor)
    vao.render(primitiva)

#Instanciando as portas de cada prÃ©dio:;
porta1 = Porta(-0.7, -0.35, 0.25, 0.3, CINZA_3)
porta2 = Porta(-0.05, -0.35, 0.25, 0.3, CINZA_3)
porta3 = Porta(0.65, -0.35, 0.25, 0.3, CINZA_3)

#Instanciando os prÃ©dios:
predio1 = Predio(-0.7, 0.10, 0.5, 1.2, CINZA_CLARO, porta1)
predio2 = Predio(-0.05, 0.20, 0.5, 1.4, CINZA_CLARO, porta2)
predio3 = Predio(0.65, 0.05, 0.5, 1.1, CINZA_CLARO, porta3)


vetor_predios = [predio1, predio2, predio3]

#Instanciando o chao, a guia e a calÃ§ada:
asfalto = Solo(0.0, -0.8, 2.0, 0.5, CINZA_ESCURO)
guia = Solo(0.0, -0.6, 2.0, 0.1, CINZA_3)
calcada = Solo(0.0, -0.5, 2.0, 0.2, CINZA_4)


#Instanciando o corpo celeste que poderÃ¡ ser o sol ou a lua:
corpo_celeste = Corpo_celeste(0.8, 0.8, 0.15, 0.15, AMARELO)

while not glfw.window_should_close(janela):
    # Uma escrita por quadro: os cinco desenhos abaixo leem este mesmo valor.
    ajustar('u_atenuacao', 0.35 if noite else 1.0)

    ctx.clear(*(FUNDO_NOITE if noite else FUNDO_DIA))
    
    corpo_celeste.cor = (BRANCO if noite else AMARELO)
    
    desenhar(vao_circulo, corpo_celeste.obter_escala(), corpo_celeste.obter_coordenadas(), corpo_celeste.cor, moderngl.TRIANGLE_FAN)
    
    desenhar(vao_retangulo, asfalto.obter_escala(), asfalto.obter_coordenadas(), asfalto.cor, moderngl.TRIANGLES)
    
    desenhar(vao_retangulo, guia.obter_escala(), guia.obter_coordenadas(), guia.cor, moderngl.TRIANGLES)
    
    desenhar(vao_retangulo, calcada.obter_escala(), calcada.obter_coordenadas(), calcada.cor, moderngl.TRIANGLES)
    
    for i in range(len(vetor_predios)):
        desenhar(vao_retangulo, vetor_predios[i].obter_escala(), vetor_predios[i].obter_coordenadas(), vetor_predios[i].cor, moderngl.TRIANGLES)
        desenhar(vao_retangulo, vetor_predios[i].porta.obter_escala(), vetor_predios[i].porta.obter_coordenadas(),
                 vetor_predios[i].porta.cor, moderngl.TRIANGLES)
    
    
    #desenhar(vao_coracao, ESCALA_CORPO, (0.0, 0.0), MAGENTA, moderngl.TRIANGLE_FAN)

    # A mesma geometria de circulo, quatro vezes, so mudando os uniformes.
    """
    for lado in (-1.0, 1.0):
        centro = (lado * CENTRO_OLHO[0], CENTRO_OLHO[1])
        desenhar(vao_circulo, ESCALA_OLHO, centro, BRANCO_OLHO, moderngl.TRIANGLE_FAN)
        desenhar(vao_circulo, ESCALA_PUPILA,
                 (centro[0] + olhar_x, centro[1] + olhar_y), PRETO, moderngl.TRIANGLE_FAN)
    """
    
    glfw.swap_buffers(janela)
    glfw.poll_events()

for recurso in (vao_coracao, vao_circulo, vao_retangulo, vbo_coracao, vbo_circulo, vbo_retangulo, ebo_retangulo, prog):
    recurso.release()
glfw.terminate()
print("Execucao finalizada.")
