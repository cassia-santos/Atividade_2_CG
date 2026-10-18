# Atividade 2 de Computação Gráfica

Cena 2D interativa feita em Python, GLFW, ModernGL e NumPy. O projeto usa
OpenGL 4.0 Core e lê os shaders GLSL da pasta `Versao_final/shaders`.

## Executar

Use o ambiente Python já configurado para a disciplina. Execute a partir da
pasta `Versao_final`:

```bash
python main.py
```

## Controles

| Tecla | Ação |
| --- | --- |
| Setas para cima/baixo | Movem o carro pela pista |
| D | Alterna dia e noite |
| C | Troca as cores do prédio central e do carro |
| L | Liga ou desliga a lâmpada do poste |
| Esc | Fecha a janela |

O carro avança sempre à direita com velocidade horizontal constante, calculada
com o tempo decorrido entre quadros. Ao sair pela direita, reaparece à esquerda.
Retângulos e círculos compõem o carro e os demais objetos. As duas malhas são
reutilizadas com `TRIANGLES` e `TRIANGLE_FAN`. O vertex shader aplica escala e
deslocamento. O fragment shader atenua a cena à noite e calcula a luz do poste
pela distância até a lâmpada.

## Relatório e arquitetura

O [relatório no Overleaf](https://pt.overleaf.com/read/vwpshgqgddxn#ae8d76)
reúne a explicação da atividade. A [documentação C4](arquitetura_c4.md)
resume a organização do código e o caminho do desenho até a tela.
