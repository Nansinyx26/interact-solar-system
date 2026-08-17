/**
 * Constantes globais da versão web.
 *
 * Espelha o config.py do aplicativo desktop: escalas da cena, limiares de
 * detecção e parâmetros de animação. Nenhum outro módulo deve ter valor mágico.
 */

// ---------------------------------------------------------------------------
// Versão
// ---------------------------------------------------------------------------
// Uma única versão para as DUAS implementações (desktop e web). Ao alterar
// qualquer uma delas, suba este número aqui E em config.py — o
// verificar_paridade.py falha se os dois ficarem diferentes, e o publicar.py
// regenera o ZIP de download com a versão nova.
export const VERSAO = "1.5.0";

// Destino do botão "Baixar versão desktop".
//
// O pacote com o executável tem ~107 MB e o limite por arquivo estático do
// Vercel é 100 MB no plano Hobby — por isso ele NÃO é servido junto do site.
// Fica como asset de GitHub Releases (que aceita até 2 GB) e o botão aponta
// para lá. O caminho ".../releases/latest/download/..." resolve sempre para o
// release mais recente, então esta URL não precisa mudar a cada versão.
//
// Deixar vazio faz o botão servir o arquivo local gerado pelo empacotar_web.py
// (útil ao rodar o site localmente, onde não há limite de tamanho).
export const URL_DOWNLOAD_EXECUTAVEL =
  "https://github.com/Nansinyx26/interact-solar-system-exe/releases/latest/download/sistema-solar-gestos.zip";
export const ARQUIVO_DOWNLOAD_LOCAL = "sistema-solar-gestos.zip";
export const REPOSITORIO_GITHUB = "Nansinyx26/interact-solar-system-exe";

// ---------------------------------------------------------------------------
// Escalas da cena — ATENÇÃO: NÃO SÃO REALISTAS (e nem podem ser)
// ---------------------------------------------------------------------------
// Em escala linear real o Sistema Solar é indesenhável: se a órbita de Netuno
// (30,07 UA) coubesse na tela, Mercúrio (0,387 UA) ficaria a ~1% do raio, colado
// no Sol, e a Terra teria menos de 1 pixel. Usamos duas compressões:
//
// 1) RAIO ORBITAL — escala LOGARÍTMICA sobre ln(distância em UA).
// 2) RAIO DO CORPO — LEI DE POTÊNCIA com expoente 0,40.
// 3) O Sol tem raio FIXO, senão engoliria as primeiras órbitas.
//
// Os números reais, sem compressão, aparecem sempre na ficha do planeta.
export const RAIO_ORBITA_MIN_PX = 95;
export const RAIO_ORBITA_MAX_PX = 420;
export const RAIO_PLANETA_BASE_PX = 10;
export const EXPOENTE_RAIO_CORPO = 0.4;
export const RAIO_SOL_PX = 46;

// Altura de referência do enquadramento: o zoom escala junto com a janela.
export const ALTURA_REFERENCIA = 800;

// ---------------------------------------------------------------------------
// Tempo da simulação
// ---------------------------------------------------------------------------
// Quantos dias astronômicos passam por segundo real. Os períodos orbitais são
// proporcionais aos reais (Terra = referência).
export const TIME_SCALE = 12;
export const TIME_SCALE_MIN = 0.5;
export const TIME_SCALE_MAX = 400;
export const FATOR_AJUSTE_TEMPO = 1.5;
// Rotação própria comprimida: na proporção real Júpiter (9,93 h) seria um borrão.
export const FATOR_ROTACAO_PROPRIA = 0.06;

// Velocidade aparente das luas. O período de cada uma vira
// REFERENCIA * (período_real ** EXPOENTE): o expoente < 1 comprime a faixa
// (Fobos 0,3 dia e Calisto 16,7 dias ficam ambos legíveis) e a referência
// escolhe onde essa faixa cai. Com 130 e 0,38, uma volta leva de 7 a 31 s na
// escala de tempo padrão — dá para ler o nome da lua antes de ela dar a volta.
export const PERIODO_LUA_REFERENCIA_DIAS = 130.0;
export const EXPOENTE_PERIODO_LUA = 0.38;

// ---------------------------------------------------------------------------
// Câmera
// ---------------------------------------------------------------------------
export const ZOOM_VISAO_GERAL = 0.9;
export const ZOOM_MIN = 0.35;
export const ZOOM_MAX = 6.0;
export const RAIO_ALVO_FOCO_PX = 92;
export const DURACAO_TRANSICAO_S = 0.8;
// Ao focar, o corpo é deslocado para a DIREITA: a ficha ocupa a coluna
// esquerda, então o alvo precisa fugir dela, não do lado oposto.
export const DESLOCAMENTO_FOCO_X_PX = 150;
export const FATOR_ZOOM_RODA = 1.15;

// ---------------------------------------------------------------------------
// Renderização
// ---------------------------------------------------------------------------
export const COR_FUNDO = "#060710";
export const COR_ORBITA = "78, 88, 120";
export const COR_ORBITA_FOCADA = "150, 200, 255";
export const ALPHA_ORBITA_NORMAL = 0.28;
export const ALPHA_ORBITA_TENUE = 0.09;
export const ALPHA_ORBITA_FOCADA = 0.75;
export const ALPHA_CORPO_ESMAECIDO = 0.28;

export const RAIO_TEXTURA_PX = 48;
export const QUADROS_ROTACAO = 24;
export const LARGURA_TIRA_EM_RAIOS = 4;
export const FAIXAS_GIGANTE_GASOSO = 9;
export const FAIXAS_ROCHOSO = 3;
export const ESCALA_RUIDO_TEXTURA = 10;
export const INTENSIDADE_TURBULENCIA = 2.6;
export const ALPHA_SOMBRA_MAX = 0.8;

export const CAMADAS_ESTRELAS = 3;
export const ESTRELAS_POR_CAMADA = 130;
export const FATOR_PARALLAX = [0.015, 0.045, 0.1];
export const SEMENTE_ALEATORIA = 20260813;

export const FATOR_ANEL_INTERNO = 1.35;
export const FATOR_ANEL_EXTERNO = 2.3;
export const ACHATAMENTO_ANEL = 0.28;
export const INCLINACAO_ANEL_GRAUS = -12;
export const COR_ANEL_SATURNO = "226, 206, 168";
export const FATOR_ANEL_URANO_INTERNO = 1.55;
export const FATOR_ANEL_URANO_EXTERNO = 1.8;
export const ACHATAMENTO_ANEL_URANO = 0.3;
export const INCLINACAO_ANEL_URANO_GRAUS = 82;
export const COR_ANEL_URANO = "176, 224, 230";
export const COMPRIMENTO_EIXO_URANO = 2.2;

export const FATOR_HALO_SOL = 3.2;
export const COR_ANEL_DESTAQUE = "140, 210, 255";
export const FOLGA_ANEL_DESTAQUE_PX = 14;

// ---------------------------------------------------------------------------
// Webcam e detecção de mãos
// ---------------------------------------------------------------------------
// Os artefatos do MediaPipe vêm do CDN por padrão. Para servir tudo do próprio
// domínio (deploy 100% offline), baixe os dois caminhos abaixo para web/vendor/
// e troque as constantes — o resto do código não muda.
export const URL_WASM_MEDIAPIPE =
  "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@1.0.1/wasm";
export const URL_MODELO_MAOS =
  "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task";

export const MAX_MAOS = 2;
// Confiança baixa de propósito: 6, 7 e 8 exigem DUAS mãos, e a segunda costuma
// aparecer menor/mais inclinada. O filtro de verdade é a votação por maioria.
export const CONFIANCA_MIN_DETECCAO = 0.5;
export const CONFIANCA_MIN_PRESENCA = 0.5;
export const CONFIANCA_MIN_RASTREIO = 0.5;
// Throttle do PREVIEW da webcam (o desenho do vídeo + esqueleto no canto). É só
// feedback visual: a 30 Hz ninguém percebe diferença para 60, e o tempo que
// sobra vai para a cena.
export const DETECTAR_A_CADA_N_FRAMES = 2;

// Intervalo MÍNIMO entre duas inferências, em segundos.
//
// A inferência era agendada por contagem de frames de render ("1 a cada 2"), e
// isso amarrava a resposta do gesto ao FPS: num celular a 24 fps saíam 12
// leituras/s, e as 10 leituras que o estabilizador exige para confirmar um
// gesto passavam de ~0,5 s para ~0,9 s. Justamente no aparelho mais fraco o app
// ficava mais lento para obedecer.
//
// Amarrado ao RELÓGIO, o ritmo de leitura é o mesmo em qualquer dispositivo: a
// confirmação leva ~0,5 s no desktop e no celular. O teto de 30 Hz continua
// valendo (a webcam entrega ~30 fps, e o detector já descarta frame repetido),
// então isto não aumenta o custo de CPU em tela rápida — só remove a espera
// artificial em tela lenta.
export const INTERVALO_DETECCAO_S = 1 / 30;

export const LARGURA_CAPTURA = 640;
export const ALTURA_CAPTURA = 480;

// O MediaPipe extrapola landmarks para fora de [0, 1] mesmo com a mão inteira
// visível; com margem apertada e duas mãos no quadro quase tudo era descartado
// e a contagem nunca passava de 5.
export const MARGEM_QUADRO = 0.06;
export const MAX_LANDMARKS_FORA_DO_QUADRO = 3;
export const LIMIAR_AVISO_CONFIANCA = 0.72;

// Score de handedness abaixo do qual a mão é considerada lixo. O MediaPipe
// continua devolvendo 21 landmarks quando "acha" que viu uma mão numa cortina ou
// num rosto, e esses frames é que produziam a troca de gesto sozinha. Em vez de
// zerar a leitura (que apagaria o modo lua), o leitor REAPROVEITA a última pose
// boa por alguns frames — ver JANELA_REAPROVEITAMENTO_S.
export const CONFIANCA_MIN_UTIL = 0.7;
// Por quanto tempo a última pose válida pode substituir frames ruins. Acima
// disso a mão provavelmente saiu mesmo, e insistir seria mentir para o usuário.
export const JANELA_REAPROVEITAMENTO_S = 0.35;

// ---------------------------------------------------------------------------
// Filtro de landmarks (One Euro)
// ---------------------------------------------------------------------------
// O tremor natural da mão vale alguns pixels por frame e é justamente o que faz
// um dedo na fronteira do limiar piscar entre "aberto" e "fechado". Filtrar os
// 21 pontos ANTES de qualquer classificação resolve o problema na origem.
//
// Escolhemos o One Euro em vez de uma EMA simples porque a EMA obriga a um
// compromisso ruim: alpha baixo (suave) atrasa o gesto, alpha alto (responsivo)
// deixa passar o tremor. O One Euro varia o alpha com a VELOCIDADE — parado ele
// filtra forte, em movimento ele solta — então dá as duas coisas.
export const FILTRO_LANDMARKS_ATIVO = true;
// Frequência de corte com a mão parada. Quanto menor, mais estável (e mais
// "arrastado"). 1,2 Hz remove o tremor sem que o usuário perceba atraso.
export const UM_EURO_CORTE_MINIMO_HZ = 1.2;
// Quanto o corte sobe por unidade de velocidade. É o botão da responsividade:
// alto demais e o filtro deixa de agir durante o movimento.
export const UM_EURO_BETA = 0.7;
// Corte do filtro aplicado à própria derivada (padrão do artigo original).
export const UM_EURO_CORTE_DERIVADA_HZ = 1.0;
// Alternativa simples, usada quando FILTRO_LANDMARKS_ATIVO é desligado ou
// quando não há timestamp confiável: média móvel exponencial pura.
export const ALPHA_EMA_LANDMARKS = 0.4;

// ---------------------------------------------------------------------------
// Contagem de dedos (limiares em frações do tamanho da palma)
// ---------------------------------------------------------------------------
export const LIMIAR_DEDO_ESTENDIDO = 0.16;
export const LIMIAR_POLEGAR_ESTENDIDO = 0.26;
// HISTERESE: um dedo já contado como estendido só volta a "fechado" abaixo de um
// limiar MENOR. Com limiar único, um dedo parado exatamente na fronteira alterna
// a cada frame e a contagem oscila entre 3 e 4 sem o usuário mexer a mão.
// A folga é multiplicativa para acompanhar a normalização pela palma.
export const FOLGA_HISTERESE_DEDO = 0.72; // 0,16 -> sai em 0,115
export const FOLGA_HISTERESE_POLEGAR = 0.78; // 0,26 -> sai em 0,203
export const MARGEM_ZONA_CINZENTA_POLEGAR = 0.1;
export const RAZAO_POLEGAR_ABERTO = 1.02;
export const TAMANHO_PALMA_MINIMO = 1e-4;

// ---------------------------------------------------------------------------
// Estabilização temporal do gesto
// ---------------------------------------------------------------------------
// O buffer guarda LEITURAS (inferências), não frames: ~15 leituras/s, então
// 10 leituras com maioria de 70% (7 votos) equivalem a ~0,5 s de gesto firme.
export const TAMANHO_BUFFER_GESTOS = 10;
export const FRACAO_MAIORIA = 0.7;
export const COOLDOWN_TROCA_S = 0.8;
export const SEGUNDOS_ATE_VISAO_GERAL = 6;

// Gesto de comando: as duas mãos abertas (5 + 5) reenquadram o sistema.
export const GESTO_VISAO_GERAL = 10;
// A partir daqui é impossível com uma mão só — é o que dispara a dica
// "use as duas mãos" no HUD quando a leitura chega em 5.
export const GESTO_MINIMO_DUAS_MAOS = 6;

// ---------------------------------------------------------------------------
// Luas dos demais planetas ("modo luas")
// ---------------------------------------------------------------------------
// Os gestos de 0 a 10 estão todos ocupados, então as luas menores não têm
// número próprio: aparecem em bloco quando o modo é ligado — pela tecla M ou
// pelo gesto das DUAS mãos em pinça, o único ainda livre.
// Ligadas por padrão: as luas são conteúdo, não um extra escondido atrás de
// um atalho. Na visão geral elas aparecem comprimidas (FATOR_LUA_COMPACTO_*).
export const LUAS_VISIVEIS_PADRAO = true;
// Raio desenhado de uma lua do TAMANHO DA NOSSA, em pixels de mundo. Não é mais
// o raio de todas: ver EXPOENTE_RAIO_LUA logo abaixo.
export const RAIO_LUA_MENOR_PX = 2.2;
// Zoom a partir do qual as luas usam o raio orbital cheio. Abaixo dele o
// sistema é comprimido (ver FATOR_LUA_COMPACTO_*), não escondido.
export const ZOOM_MINIMO_PARA_LUAS = 1.6;

// --- tamanho desenhado da lua ----------------------------------------------
// Mesma lei de potência dos planetas (expoente < 1 comprime a faixa), com a
// nossa Lua como referência. Antes TODAS as luas tinham 2,2 px: Titã (5.150 km)
// e Fobos (22 km) saíam idênticos na tela, e comparar tamanhos é justamente o
// que se espera de um sistema de luas desenhado lado a lado.
//
// Em escala real a razão Ganimedes/Fobos é 234x; com expoente 0,32 ela vira
// 5,7x — Fobos continua sendo um ponto e Ganimedes um disco, sem que nenhum dos
// dois saia da tela. Os números reais estão sempre na ficha.
export const DIAMETRO_LUA_REFERENCIA_KM = 3474.0; // a nossa Lua
export const EXPOENTE_RAIO_LUA = 0.32;
// Pisos e tetos em pixels de mundo: abaixo de ~1,1 px a lua vira ruído de
// antisserrilhado e acima de ~3,4 px ela começa a competir com o planeta.
// O piso foi calibrado para NÃO achatar a faixa média: com 1,25 as luas de gelo
// de 400-500 km (Encélado, Miranda, Proteu) caíam todas nele e saíam do mesmo
// tamanho de Fobos, que tem 22 km. Com 1,10 só as cinco realmente minúsculas
// ficam no piso, e é o que se espera — elas são pontos mesmo.
export const RAIO_LUA_MENOR_MIN_PX = 1.1;
export const RAIO_LUA_MENOR_MAX_PX = 3.4;

// --- sprite esférico da lua -------------------------------------------------
// Cada lua deixou de ser um círculo de cor chapada: ganha um sprite
// pré-renderizado com manchas de terreno, escurecimento de limbo e borda suave,
// mais um terminador dia/noite apontado para o Sol — as mesmas três coisas que
// já davam volume aos planetas.
export const RAIO_TEXTURA_LUA_PX = 20;
export const ALPHA_SOMBRA_LUA = 0.65;
// Contraste das manchas de terreno, como fração da distância entre corEscura e
// corClara. Alto demais e toda lua vira Jápeto.
export const CONTRASTE_TERRENO_LUA = 0.62;
// Blocos da primeira oitava do ruído da lua — bem menos que os 10 dos planetas.
// O sprite tem 40 px de lado: com 10 blocos as manchas ficam com 4 px e somem
// no primeiro downscale, que é o caso normal (a lua raramente passa de 8 px na
// tela). Com 4 blocos as manchas têm 10 px e sobrevivem à redução.
export const ESCALA_RUIDO_LUA = 4;

// --- legibilidade dos rótulos de lua ---------------------------------------
// O nome era desenhado direto sobre a cena. Contra o campo de estrelas passava,
// mas em cima do disco de Júpiter (bege claro) ou dos anéis de Saturno um texto
// cinza de 11 px some. Agora todo rótulo sai com um contorno escuro atrás — é o
// mesmo truque de legenda de mapa, e no Canvas custa um strokeText.
export const ALPHA_ROTULO_LUA = 0.8;
export const COR_CONTORNO_ROTULO = "6, 8, 18";
export const ESPESSURA_CONTORNO_ROTULO_PX = 2;
// Distância mínima entre dois nomes de lua na tela. Abaixo dela o segundo é
// omitido: com Júpiter comprimido na visão geral, cinco rótulos empilhados no
// mesmo ponto viram uma mancha ilegível — e nenhum deles é lido. O rótulo da lua
// em DESTAQUE nunca é omitido, porque ele é a resposta ao gesto do usuário.
export const DISTANCIA_MINIMA_ROTULO_LUA_PX = 26.0;

// Raio orbital COMPACTO, usado na visão geral — múltiplo do raio do planeta.
// Sem isso as luas invadem o planeta vizinho: em volta de Júpiter elas
// precisariam de 105 px e só há 70 px até Saturno. Com teto de 1,45 todo mundo
// cabe (Júpiter usa 38 px, a Lua da Terra usa 14,5 contra 34 de folga).
export const FATOR_LUA_COMPACTO_MIN = 1.15;
export const FATOR_LUA_COMPACTO_MAX = 1.45;
// Planetas com anéis precisam de um piso: com o fator compacto puro, as luas de
// Saturno cairiam DENTRO dos anéis, que vão até 2,3 raios.
export const FOLGA_LUA_APOS_ANEL = 0.15;
export const COR_ORBITA_LUA = "150, 160, 190";
export const ALPHA_ORBITA_LUA = 0.18;

// ---------------------------------------------------------------------------
// Cinturão de asteroides
// ---------------------------------------------------------------------------
// Fica entre Marte (1,52 UA) e Júpiter (5,20 UA). Como o raio orbital do
// projeto é logarítmico, a faixa é calculada em nucleo/orbita.js a partir
// destas distâncias reais.
export const CINTURAO_UA_INTERNO = 2.06;
export const CINTURAO_UA_EXTERNO = 3.27;
export const ASTEROIDES_DESENHADOS = 340;
export const COR_ASTEROIDE = "150, 138, 120";
export const ALPHA_ASTEROIDE_MIN = 0.24;
export const ALPHA_ASTEROIDE_MAX = 0.67;
// O cinturão gira devagar, como um corpo só: seguir o período real de cada
// asteroide não mudaria nada visualmente e custaria uma volta por partícula.
export const PERIODO_CINTURAO_DIAS = 1680.0;

// ---------------------------------------------------------------------------
// Gesto "L" — modificador de modo (seleção de luas)
// ---------------------------------------------------------------------------
// Uma mão em "L" faz o número da OUTRA mão significar índice de lua em vez de
// planeta. Foi a saída para um limite duro: a contagem vai de 0 a 10 e todos os
// valores já estão ocupados — não sobrava número, mas sobrava forma.
//
// Faixa angular entre polegar e indicador. Abaixo de 50° o gesto vira "apontar"
// e acima de 130° a mão está praticamente aberta; nos dois casos não é um L.
export const ANGULO_L_MINIMO_GRAUS = 50.0;
export const ANGULO_L_MAXIMO_GRAUS = 130.0;
// Histerese ASSIMÉTRICA de propósito: entrar devagar incomoda menos que sair
// sem querer no meio de uma seleção.
export const FRAMES_PARA_ENTRAR_MODO_LUAS = 6;
export const FRAMES_PARA_SAIR_MODO_LUAS = 8;
// Votação da lua escolhida, no mesmo espírito do estabilizador de planetas.
export const BUFFER_SELECAO_LUA = 6;
export const VOTOS_SELECAO_LUA = 5;
// Cooldown após ABRIR uma ficha de lua. Mais longo que o do estabilizador de
// planetas porque a ficha muda a tela inteira: reabrir outra em seguida, por um
// frame ruim, é bem mais incômodo que trocar de planeta sem querer.
export const COOLDOWN_SELECAO_LUA_S = 0.8;

// --- confirmação da lua (PREVIEW -> FICHA) ---------------------------------
// Enquanto o "L" é mantido, o número da outra mão apenas PRÉ-VISUALIZA a lua
// (destaque na órbita + nome no HUD). A ficha só abre quando o mesmo número se
// mantém estável por FRAMES_PARA_ABRIR_FICHA_LUA leituras seguidas.
//
// São leituras (inferências), não frames de render: a ~15 leituras/s, 12
// leituras ≈ 0,8 s de mão parada. O valor foi escolhido para ser longo o
// bastante para o usuário "passear" pelos números sem abrir nada, e curto o
// bastante para não cansar o braço.
export const FRAMES_PARA_ABRIR_FICHA_LUA = 12;
// Tolerância a falhas DENTRO da contagem: um único frame com número diferente
// não zera o progresso, só o desconta. Sem isso, uma piscada do rastreio no
// décimo frame obrigava a recomeçar do zero.
export const FALHAS_TOLERADAS_CONFIRMACAO = 3;

// ---------------------------------------------------------------------------
// Gesto de pinça — zoom controlado pela câmera
// ---------------------------------------------------------------------------
// Distância ponta do polegar <-> ponta do indicador dividida pelo tamanho da
// palma, o que torna a medida independente da distância até a câmera.
//
// Histerese: entra em modo zoom abaixo de ATIVA e só sai acima de SAIDA. Com um
// limiar único a pinça piscaria na fronteira e o zoom entraria e sairia sozinho.
export const LIMIAR_PINCA_ATIVA = 0.38;
export const LIMIAR_PINCA_SAIDA = 0.55;
// Peso do valor novo na média móvel exponencial: sem filtro o zoom vibra com o
// tremor natural da mão.
export const SUAVIZACAO_PINCA = 0.35;
// Trava saltos quando o rastreio perde a mão por um instante.
export const FATOR_ZOOM_PINCA_MAX = 1.12;
// Sair da pinça passa por poses lidas como 1, 2 ou 3 dedos; sem esta pausa o
// zoom terminaria trocando de planeta.
export const COOLDOWN_APOS_PINCA_S = 0.6;

// ---------------------------------------------------------------------------
// Narração por voz (TTS)
// ---------------------------------------------------------------------------
export const NARRACAO_ATIVA_PADRAO = true;
export const IDIOMA_NARRACAO = "pt-BR";
// A Web Speech API usa 1 como velocidade natural; 175 ppm do pyttsx3 equivale a
// ~1,05 aqui. A constante compartilhada é a do desktop, convertida no narrador.
export const VELOCIDADE_NARRACAO = 175;
export const VOLUME_NARRACAO = 0.9;
// A narração lê a ficha inteira: nome, tipo, diâmetro, distância, períodos,
// luas, temperatura e o fato curioso. Desligado, fala só o nome e o tipo.
export const NARRAR_FICHA_COMPLETA = true;

// --- ElevenLabs (voz neural) ------------------------------------------------
// A chave da API JAMAIS pode chegar ao navegador: o front é público e qualquer
// visitante leria o valor. Por isso o site não fala com a ElevenLabs direto —
// ele chama /api/voz, uma função serverless que guarda a chave no ambiente do
// servidor (variável ELEVENLABS_API_KEY nas configurações do Vercel).
//
// Sem a função publicada (site aberto localmente, por exemplo) ou em caso de
// erro, o narrador cai para a voz do próprio navegador.
export const ENDPOINT_VOZ = "/api/voz";
export const ELEVENLABS_VOZ_NOME = "Brian";
// Servidor Backend no Render.com (para comunicação direta ou fallback entre Vercel e Render)
export const URL_SERVIDOR_RENDER = "https://sistema-solar-backend.onrender.com";


// ---------------------------------------------------------------------------
// Lua (satélite da Terra)
// ---------------------------------------------------------------------------
// Raio orbital da Lua em torno da Terra, em pixels de mundo. Não segue a escala
// logarítmica dos planetas — seria invisível. É um valor visual fixo.
export const RAIO_ORBITA_LUA_PX = 28;
// Raio desenhado da Lua (fixo, como o Sol). Em escala real seria ~0,27x a Terra,
// mas com raio base 10 px isso daria 2,7 px — pequeno demais para ver textura.
export const RAIO_LUA_PX = 4;

