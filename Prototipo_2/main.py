"""Cidade 2D com carro animado e iluminação local no poste.

Execute: python main.py
Setas para cima/baixo mudam a posição vertical do carro; D alterna dia/noite;
C troca as cores do prédio central e do carro; L liga/desliga o poste; Esc sai.

OBS.: A implementação da geometria do retângulo foi baseada no código 05u_quadrado_uniform.py
disponibilizado pelo professor. Assim, as coordenadas foram adaptas para formar
os retângulos necessários, e o ebo foi utilizado para reaproveitar vértices.
"""
import sys
from pathlib import Path

import glfw
import moderngl
import numpy as np

# As classes guardam os dados dos objetos; o desenho fica neste arquivo.
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
BRANCO = (1.0, 1.0, 1.0, 1.0)
PRETO = (0.05, 0.05, 0.05, 1.0)
FUNDO_DIA = (0.67, 0.84, 0.9, 1.0)
FUNDO_NOITE = (0.05, 0.05, 0.12, 1.0)
VERDE = (0.16, 0.55, 0.31, 1.0)
MARROM = (0.40, 0.25, 0.13, 1.0)
AZUL_JANELA = (0.22, 0.45, 0.62, 1.0)
LUZ_JANELA = (1.0, 0.78, 0.35, 1.0)
CORES_PREDIO = (CINZA_CLARO, (0.55, 0.43, 0.60, 1.0), (0.40, 0.58, 0.53, 1.0))
CORES_CARRO = ((0.83, 0.16, 0.13, 1.0), (0.16, 0.43, 0.78, 1.0), (0.96, 0.59, 0.13, 1.0))

VELOCIDADE_CARRO = 0.35  # unidades da cena por segundo, sempre para a direita
VELOCIDADE_VERTICAL = 0.28
LIMITE_INFERIOR = -0.89
LIMITE_SUPERIOR = -0.72
POSICAO_POSTE = (0.51, 0.08)
RAIO_LUZ = 1.05


def leque(x, y):
    """Põe o centro antes da borda e fecha o contorno para TRIANGLE_FAN."""
    x = np.concatenate(([0.0], x, [x[0]]))
    y = np.concatenate(([0.0], y, [y[0]]))
    return np.column_stack((x, y, np.zeros_like(x), np.ones_like(x))).astype('f4')


def curva_circulo(n=48):
    """Amostra a circunferência usada por rodas, copa, sol e lua."""
    t = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    return leque(np.cos(t), np.sin(t))


def curva_retangulo():
    """Cria quatro vértices para retângulos de qualquer tamanho."""
    return np.array([
        -0.5, -0.5, 0.0, 1.0,
         0.5, -0.5, 0.0, 1.0,
         0.5,  0.5, 0.0, 1.0,
        -0.5,  0.5, 0.0, 1.0,
    ], dtype='f4')


def indices_retangulo():
    """Forma dois triângulos com os quatro vértices do retângulo."""
    return np.array([0, 1, 2, 2, 3, 0], dtype='u4')


def erro_glfw(codigo, descricao):
    """Mostra a descrição de erros do GLFW no terminal."""
    print(f"GLFW [{codigo}]: {descricao}", file=sys.stderr)


# O callback precisa estar ativo antes da criação da janela.
glfw.set_error_callback(erro_glfw)

if not glfw.init():
    sys.exit("FALHA: glfw nao inicializou")

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 0)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
# A janela quadrada conserva os círculos sem correção de aspecto.
glfw.window_hint(glfw.SAMPLES, 4)
glfw.window_hint(glfw.RESIZABLE, False)

janela = glfw.create_window(640, 640, "Cidade com carro", None, None)
if not janela:
    glfw.terminate()
    sys.exit("FALHA: nao foi possivel criar a janela")

glfw.make_context_current(janela)
glfw.swap_interval(1)
ctx = moderngl.create_context()
if ctx.version_code < 400:
    glfw.terminate()
    sys.exit("FALHA: OpenGL 4.0 Core ou superior e necessario")

# O driver pode entregar menos amostras de suavização do que foi pedido.
print(f"amostras por pixel obtidas: {ctx.screen.samples}")

prog = ctx.program(
    vertex_shader=(SHADERS / "cidade.vert").read_text(encoding="utf-8"),
    fragment_shader=(SHADERS / "cidade.frag").read_text(encoding="utf-8"),
)
# O halo e a mancha de luz no asfalto precisam de transparência.
ctx.enable(moderngl.BLEND)
ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA


def montar(vertices, ebo):
    """Envia vértices para a GPU e associa seu formato ao shader."""
    vbo = ctx.buffer(vertices.tobytes())
    if ebo is None:
        vao = ctx.vertex_array(prog, [(vbo, '4f', 'vPosition')])
    else:
        vao = ctx.vertex_array(prog, [(vbo, '4f', 'vPosition')], index_buffer=ebo)

    return vbo, vao


ebo_retangulo = ctx.buffer(indices_retangulo().tobytes())

vbo_circulo, vao_circulo = montar(curva_circulo(), None)
vbo_retangulo, vao_retangulo = montar(curva_retangulo(), ebo_retangulo)

# O avanço horizontal é automático; a pessoa controla apenas a altura.
carro_x, carro_y = -0.72, -0.81
cor_carro = CORES_CARRO[0]
noite = False
indice_cor_predio = 0
lampada_acesa = True


def tecla(window, key, scancode, action, mods):
    """Troca os estados discretos apenas quando uma tecla é pressionada."""
    global noite, indice_cor_predio, lampada_acesa, cor_carro
    if action != glfw.PRESS:
        return

    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)
    elif key == glfw.KEY_D:
        noite = not noite
    elif key == glfw.KEY_C:
        indice_cor_predio = (indice_cor_predio + 1) % len(CORES_PREDIO)
        predio2.cor = CORES_PREDIO[indice_cor_predio]
        cor_carro = CORES_CARRO[indice_cor_predio]
    elif key == glfw.KEY_L:
        lampada_acesa = not lampada_acesa


glfw.set_key_callback(janela, tecla)


def ajustar(nome, valor):
    """Envia um valor ao shader e acusa a falta da uniforme esperada."""
    prog[nome].value = valor


def desenhar(vao, escala, deslocamento, cor, primitiva, emissao=0.0, halo=0.0):
    """Reaproveita a malha com novos tamanho, posição, cor e brilho."""
    ajustar('u_escala', escala)
    ajustar('u_deslocamento', deslocamento)
    ajustar('u_cor', cor)
    ajustar('u_emissao', emissao)
    ajustar('u_halo', halo)
    vao.render(primitiva)


def criar_janelas(predio, linhas):
    """Distribui janelas na fachada sem criar outra malha na GPU."""
    x, y = predio.obter_coordenadas()
    _, altura = predio.obter_escala()
    base = y - altura / 2 + 0.40
    for linha in range(linhas):
        for coluna, deslocamento in enumerate((-0.14, 0.0, 0.14)):
            acesa = (linha + coluna) % 3 != 0
            predio.janelas.append((x + deslocamento, base + linha * 0.18, acesa))


def desenhar_nuvens():
    """Monta cada nuvem com três cópias da malha circular."""
    cor = CINZA_3 if noite else BRANCO
    for x, y, tamanho in ((-0.55, 0.82, 0.13), (0.21, 0.77, 0.10)):
        for dx, dy, fator in ((-0.08, 0.0, 0.9), (0.0, 0.04, 1.1), (0.09, 0.0, 0.85)):
            escala = (tamanho * fator, tamanho * fator)
            desenhar(vao_circulo, escala, (x + dx, y + dy), cor, moderngl.TRIANGLE_FAN)


def desenhar_arvores():
    """Usa um retângulo para o tronco e um círculo para a copa."""
    for x, tamanho in ((-0.39, 1.0), (0.33, 0.85)):
        desenhar(vao_retangulo, (0.035 * tamanho, 0.22 * tamanho),
                 (x, -0.30), MARROM, moderngl.TRIANGLES)
        desenhar(vao_circulo, (0.23 * tamanho, 0.23 * tamanho),
                 (x, -0.16), VERDE, moderngl.TRIANGLE_FAN)


def desenhar_poste():
    """Desenha a haste e a lâmpada que serve de fonte à luz local."""
    desenhar(vao_retangulo, (0.025, 0.52), (0.43, -0.15),
             CINZA_ESCURO, moderngl.TRIANGLES)
    desenhar(vao_retangulo, (0.10, 0.025), (0.47, 0.11),
             CINZA_ESCURO, moderngl.TRIANGLES)
    cor = AMARELO if lampada_acesa else CINZA_3
    emissao = 1.0 if noite and lampada_acesa else 0.0
    desenhar(vao_circulo, (0.075, 0.075), POSICAO_POSTE, cor,
             moderngl.TRIANGLE_FAN, emissao)


def atualizar_carro(dt):
    """Avança o carro pelo tempo real e lê as setas para mudar sua altura."""
    global carro_x, carro_y
    # O resto preserva a distância percorrida mesmo no quadro em que ele reaparece.
    carro_x = (carro_x + 1.25 + VELOCIDADE_CARRO * dt) % 2.5 - 1.25

    subir = glfw.get_key(janela, glfw.KEY_UP) == glfw.PRESS
    descer = glfw.get_key(janela, glfw.KEY_DOWN) == glfw.PRESS
    carro_y += (subir - descer) * VELOCIDADE_VERTICAL * dt
    carro_y = max(LIMITE_INFERIOR, min(LIMITE_SUPERIOR, carro_y))


def desenhar_carro():
    """Monta carroceria e cabine com retângulos e rodas com círculos."""
    desenhar(vao_retangulo, (0.34, 0.10), (carro_x, carro_y + 0.02),
             cor_carro, moderngl.TRIANGLES)
    desenhar(vao_retangulo, (0.18, 0.075), (carro_x - 0.025, carro_y + 0.10),
             cor_carro, moderngl.TRIANGLES)
    desenhar(vao_retangulo, (0.07, 0.045), (carro_x - 0.06, carro_y + 0.10),
             AZUL_JANELA, moderngl.TRIANGLES)
    desenhar(vao_retangulo, (0.055, 0.045), (carro_x + 0.035, carro_y + 0.10),
             AZUL_JANELA, moderngl.TRIANGLES)
    for deslocamento in (-0.105, 0.105):
        desenhar(vao_circulo, (0.041, 0.041),
                 (carro_x + deslocamento, carro_y - 0.044),
                 PRETO, moderngl.TRIANGLE_FAN)


def desenhar_halo():
    """Mostra o halo da lâmpada e uma mancha suave de luz no asfalto."""
    if noite and lampada_acesa:
        desenhar(vao_circulo, (0.40, 0.10), (POSICAO_POSTE[0], -0.80), AMARELO,
                 moderngl.TRIANGLE_FAN, halo=0.28)
        desenhar(vao_circulo, (0.58, 0.58), POSICAO_POSTE, AMARELO,
                 moderngl.TRIANGLE_FAN, halo=0.20)


# As instâncias guardam dados; as malhas de retângulo e círculo já estão na GPU.
porta1 = Porta(-0.7, -0.35, 0.25, 0.3, CINZA_3)
porta2 = Porta(-0.05, -0.35, 0.25, 0.3, CINZA_3)
porta3 = Porta(0.65, -0.35, 0.25, 0.3, CINZA_3)

# Cada prédio guarda sua porta para desenhá-la junto com a fachada.
predio1 = Predio(-0.7, 0.10, 0.5, 1.2, CINZA_CLARO, porta1)
predio2 = Predio(-0.05, 0.20, 0.5, 1.4, CINZA_CLARO, porta2)
predio3 = Predio(0.65, 0.05, 0.5, 1.1, CINZA_CLARO, porta3)


vetor_predios = [predio1, predio2, predio3]
criar_janelas(predio1, 4)
criar_janelas(predio2, 5)
criar_janelas(predio3, 4)

# As três faixas formam rua, guia e calçada.
asfalto = Solo(0.0, -0.8, 2.0, 0.5, CINZA_ESCURO)
guia = Solo(0.0, -0.6, 2.0, 0.1, CINZA_3)
calcada = Solo(0.0, -0.5, 2.0, 0.2, CINZA_4)


# O disco troca de cor quando o modo global muda.
corpo_celeste = Corpo_celeste(0.8, 0.8, 0.15, 0.15, AMARELO)
tempo_anterior = glfw.get_time()

while not glfw.window_should_close(janela):
    # Medir o tempo evita que a velocidade horizontal varie com o FPS.
    agora = glfw.get_time()
    dt = agora - tempo_anterior
    tempo_anterior = agora
    atualizar_carro(dt)

    # O fragment shader escurece a cena e clareia a região perto do poste.
    ajustar('u_atenuacao', 0.35 if noite else 1.0)
    ajustar('u_luz_pos', POSICAO_POSTE)
    ajustar('u_luz_raio', RAIO_LUZ)
    ajustar('u_luz_ativa', 1.0 if noite and lampada_acesa else 0.0)
    ctx.clear(*(FUNDO_NOITE if noite else FUNDO_DIA))

    # Sem teste de profundidade, o que vem depois cobre o que foi desenhado antes.
    if noite:
        for x, y in ((-0.90, 0.91), (-0.28, 0.94), (0.05, 0.91), (0.44, 0.87)):
            desenhar(vao_circulo, (0.009, 0.009), (x, y), BRANCO,
                     moderngl.TRIANGLE_FAN, 1.0)
    desenhar_nuvens()
    corpo_celeste.cor = BRANCO if noite else AMARELO
    desenhar(vao_circulo, corpo_celeste.obter_escala(),
             corpo_celeste.obter_coordenadas(), corpo_celeste.cor,
             moderngl.TRIANGLE_FAN, 1.0)

    for faixa in (asfalto, guia, calcada):
        desenhar(vao_retangulo, faixa.obter_escala(), faixa.obter_coordenadas(),
                 faixa.cor, moderngl.TRIANGLES)

    for i in range(len(vetor_predios)):
        predio = vetor_predios[i]
        desenhar(vao_retangulo, predio.obter_escala(), predio.obter_coordenadas(),
                 predio.cor, moderngl.TRIANGLES)
        desenhar(vao_retangulo, predio.porta.obter_escala(),
                 predio.porta.obter_coordenadas(), predio.porta.cor,
                 moderngl.TRIANGLES)

        # À noite, as janelas acesas mantêm a cor e as apagadas escurecem.
        for x, y, acesa in predio.janelas:
            cor = LUZ_JANELA if noite and acesa else AZUL_JANELA
            emissao = 1.0 if noite and acesa else 0.0
            desenhar(vao_retangulo, (0.075, 0.10), (x, y), cor,
                     moderngl.TRIANGLES, emissao)

    desenhar_arvores()
    desenhar_halo()
    desenhar_poste()
    desenhar_carro()

    glfw.swap_buffers(janela)
    glfw.poll_events()

# Solta os recursos da GPU antes de encerrar o GLFW.
for recurso in (vao_circulo, vao_retangulo, vbo_circulo, vbo_retangulo, ebo_retangulo, prog):
    recurso.release()
glfw.terminate()
print("Execucao finalizada.")
