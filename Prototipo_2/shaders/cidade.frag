#version 400 core
// A noite escurece a cena; a lâmpada clareia os fragmentos próximos.

in vec4 v2fcolor;
in vec2 v2fpos;
in vec2 v2flocal;
uniform float u_atenuacao;  // 1.0 de dia, menor à noite
uniform float u_emissao;     // 1.0 para objetos luminosos
uniform vec2 u_luz_pos;
uniform float u_luz_raio;
uniform float u_luz_ativa;
uniform float u_halo;
out vec4 outfragcolor;

void main() {
    float distancia = distance(v2fpos, u_luz_pos);

    // A coordenada local faz o mesmo halo servir ao círculo e à elipse no chão.
    if (u_halo > 0.0) {
        float alpha = u_halo * u_luz_ativa
                    * (1.0 - smoothstep(0.0, 1.0, length(v2flocal)));
        outfragcolor = vec4(1.0, 0.80, 0.35, alpha);
        return;
    }

    // A emissão preserva o brilho de lua, estrelas, janelas e lâmpada.
    float emissao = clamp(u_emissao, 0.0, 1.0);
    float brilho = mix(u_atenuacao, 1.0, emissao);

    // A luz local cai com a distância e recupera parte da cor no modo noite.
    float alcance = 1.0 - smoothstep(0.0, u_luz_raio, distancia);
    float luz = u_luz_ativa * alcance * (1.0 - emissao);
    vec3 cor = v2fcolor.rgb * (brilho + (1.0 - brilho) * luz);
    cor += vec3(1.0, 0.68, 0.22) * luz * 0.10;
    outfragcolor = vec4(min(cor, vec3(1.0)), v2fcolor.a);
}
