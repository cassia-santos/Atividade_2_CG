#version 400 core

// A mesma malha muda de tamanho e posição a cada chamada de desenho.

layout(location = 0) in vec4 vPosition;

uniform vec2 u_escala;
uniform vec2  u_deslocamento;
uniform vec4  u_cor;

out vec4 v2fcolor;
out vec2 v2fpos;
out vec2 v2flocal;

void main() {
    // Primeiro escala o vértice, depois desloca a malha para a cena.
    v2fpos = vPosition.xy * u_escala + u_deslocamento;
    v2flocal = vPosition.xy;
    gl_Position = vec4(v2fpos, vPosition.zw);

    v2fcolor = u_cor;
}
